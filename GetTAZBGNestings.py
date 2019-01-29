import pandas as pd
import numpy as np
import os
from datetime import datetime

def sort_share_matrix(matrix):
    '''
    Sorts a share matrix first so that columns with ones higher up are further to the left

    Parameters
    ----------
    matrix (pandas.DataFrame):
        The share matrix to be sorted

    Returns
    -------
    sorted_matrix (pandas.DataFrame):
        Sorted share matrix
    '''
    first_one = pd.Series(index = matrix.columns) #Define series to identify the index of the first one in each column
    for col in matrix.columns:
        try:
            first_one[col] = list(matrix[col]).index(1) #Identify the index of the first one in the column
        except ValueError:
            continue #If there aren't any ones in the column, leave the value in `first_one` null

    order = first_one.sort_values().index #Find order of columns so that columns with ones higher up are further to the left
    return matrix[order]

def classify_nesting(nesting):
    '''
    Classifies a nesting as one to one, one TAZ to many Block Groups, one Block Group to Many TAZs, or many to many

    Parameters
    ----------
    nesting (length-2 tuple):
        Length-2 tuple where the first element is the number of TAZs and the second is the number of block groups

    Returns
    -------
    classification (str):
        Classification name
    '''
    if nesting[0] == 1 and nesting[1] == 1:
        return 'One TAZ = One Block Group'
    else:
        if nesting[0] == 1:
            return 'One TAZ = Many Block Groups'
        elif nesting[1] == 1:
            return 'Many TAZs = One Block Group'
        else:
            return 'Many TAZs = Many Block Groups'

def classify_pop(population):
    '''
    Classifies a geography based on population into three categories: less than 600, between 600 and 3000 (bounds included), and more than 3000

    Parameters
    ----------
    population (numeric):
        Population value to classify

    Returns
    -------
    class (str):
        Population classification
    '''
    if population < 600:
        return '<600'
    elif population <= 3000:
        return '600-3000'
    else:
        return '>3000'

#Define file paths and names
start_time = datetime.now()

base_path = os.path.split(__file__)[0]
output_path = os.path.join(base_path, 'TAZ_BG_Nestings_Output_' + start_time.strftime('%y%m%d%H%M%S'))
os.mkdir(output_path)

infile = os.path.join(base_path, 'Blk_BG_TAZ_Lookup_SampleInput.csv')
taz2bg_file = os.path.join(output_path, 'taz2bg.csv')
bg2taz_file = os.path.join(output_path, 'bg2taz.csv')

print('Reading Input File')
data = pd.read_csv(infile)

tazs = data['TAZ_10'].value_counts().sort_index().index  #List of TAZs
bgs = data['BLKGRP10'].value_counts().sort_index().index #List of block groups

n_t = len(tazs) #Number of TAZs
n_b = len(bgs)  #Number of block groups

print('Creating Population and Share Matrices')
#The population matrix has the TAZs as the rows and the block groups as the columns.
#Each entry is the population in the TAZ and the block group
pop_matrix = pd.DataFrame(np.zeros((n_t, n_b)), index = tazs, columns = bgs)
for row in data.index:
    taz = data.loc[row, 'TAZ_10']
    bg = data.loc[row, 'BLKGRP10']
    pop = data.loc[row, 'POP10']
    pop_matrix.loc[taz, bg] += pop

#The "Share Matrix" has the TAZs as the rows and the block groups as the columns
#It is equal to 1 if the TAZ and the Block Group share population, and 0 if they do not, indicating if a TAZ and block group share population
share_matrix = pop_matrix.astype(bool).astype(int)
share_matrix_backup = share_matrix.copy()

#The row and column sums of the population matrix are the TAZ and block group populations, respectively
taz_pops = pop_matrix.sum(1).astype(int)
bg_pops = pop_matrix.sum(0).astype(int)

print('Removing Zero-Population TAZs and Block Groups')
#Count the number of block groups sharing population with each TAZ and TAZs sharing population with block groups
bgs_in_tazs = share_matrix.sum(1)
tazs_in_bgs = share_matrix.sum(0)

#Identify TAZs and block groups with and without population
zero_pop_tazs = bgs_in_tazs[bgs_in_tazs == 0].index
pop_tazs = bgs_in_tazs[bgs_in_tazs > 0].index
zero_pop_bgs = tazs_in_bgs[tazs_in_bgs == 0].index
pop_bgs = tazs_in_bgs[tazs_in_bgs > 0].index

#Remove zero-population TAZs and block groups from the share matrix (they will be added later)
share_matrix = share_matrix.loc[pop_tazs, pop_bgs]

print('Sorting Share Matrix')
#The share matrix is sorted so that it is almost diagional, allowing for easy grouping of TAZs and block groups into nestings
# Example:
# BG  1 2 3 4 5 6 7 8 9 10
# TAZ
# 1   1 0 0 0 0 0 0 0 0 0 (One-to-one)
# 2   0 1 0 0 0 0 0 0 0 0 (One-to-one)
# 3   0 0 1 1 1 0 0 0 0 0 (1 TAZs/3 Block Groups)
# 4   0 0 0 0 0 1 0 0 0 0 (2 TAZs/1 Block Group)
# 5   0 0 0 0 0 1 0 0 0 0 (2 TAZs/1 Block Group)
# 6   0 0 0 0 0 0 1 1 0 0 (2 TAZs/3 Block Groups)
# 7   0 0 0 0 0 0 1 1 1 0 (2 TAZs/3 Block Groups)
# 8   0 0 0 0 0 0 0 0 0 1 (3 TAZs/1 Block Group)
# 9   0 0 0 0 0 0 0 0 0 1 (3 TAZs/1 Block Group)
# 10  0 0 0 0 0 0 0 0 0 1 (3 TAZs/1 Block Group)

sort_iter = 10 #Number of sorting iterations. Multiple are needed for correct sorting
for i in range(2*sort_iter): #In each iteration sort by block groups, than by TAZs
    share_matrix = sort_share_matrix(share_matrix)
    share_matrix = share_matrix.T

print('Identifying TAZ/Block Group Nestings')
bgs = list(share_matrix.columns)
tazs = list(share_matrix.index)

n_bgs = len(bgs)
n_tazs = len(tazs)

bg_sums = share_matrix.sum(0)
taz_sums = share_matrix.sum(1)

nesting_id = 1
taz_index = 0
bg_index = 0

taz2nesting = pd.Series(index = tazs)
bg2nesting = pd.Series(index = bgs)
nestings = pd.DataFrame(columns = ['n_tazs', 'n_bgs'])

while taz_index < n_tazs or bg_index < min_bgs:

    current_taz = tazs[taz_index]
    current_bg = bgs[bg_index]

    #Identify the minimum number of block groups and TAZs needed in the nesting as the row and column sums of the share matrix for the current TAZ and block group
    min_bgs = share_matrix.loc[current_taz].sum()
    min_tazs = share_matrix[current_bg].sum()

    complete_nesting = False

    while not complete_nesting:

        more_tazs_needed = False
        more_bgs_needed = False

        #Check if more block groups need to be added to the nesting
        for taz in tazs[taz_index:(taz_index + min_tazs)]: #Check all of the current TAZs in the nesting
            test_row = share_matrix.loc[taz].copy() #Copy the row of the share matrix for testing
            test_row[bgs[bg_index:(bg_index + min_bgs)]] = 0 #Set the test row values to zero for the block groups already in the nesting
            if test_row.sum() > 0: #Check if there are additional block groups to be added, and if there are, add them
                more_bgs_needed = True
                min_bgs += test_row.sum()
                break

        #Now perform the same check, only add TAZs as necessary
        for bg in bgs[bg_index:(bg_index + min_bgs)]:
            test_col = share_matrix[bg].copy()
            test_col[tazs[taz_index:(taz_index + min_tazs)]] = 0
            if test_col.sum() > 0:
                more_tazs_needed = True
                min_tazs += test_col.sum()
                break

        #Now check if no TAZs or block groups were added. If they were, go back to the start of the while loop. If not, record the nesting.
        if not more_tazs_needed and not more_bgs_needed:
            complete_nesting = True

            taz2nesting[tazs[taz_index:(taz_index + min_tazs)]] = nesting_id
            bg2nesting[bgs[bg_index:(bg_index + min_bgs)]] = nesting_id

            nestings.loc[nesting_id] = [min_tazs, min_bgs]

            nesting_id += 1

            taz_index += min_tazs
            bg_index += min_bgs

print('Classifying TAZ/Block Group Nestings')
nestings['nesting'] = list(zip(nestings['n_tazs'], nestings['n_bgs'])) #Create tuples with # of TAZs and # of block groups
nestings['type'] = nestings['nesting'].apply(classify_nesting)

max_tazs = nestings['n_tazs'].max()
max_bgs = nestings['n_bgs'].max()

taz2nesting = pd.DataFrame(taz2nesting)
taz2nesting['nesting_id'] = taz2nesting[0]
del taz2nesting[0]
taz2nesting.index.name = 'taz_id'

taz2nesting = taz2nesting.reset_index()
taz2nesting['pop'] = taz2nesting['taz_id'].map(taz_pops)
taz2nesting['nest_type'] = taz2nesting['nesting_id'].map(nestings['type'])
taz2nesting['pop_class'] = taz2nesting['pop'].apply(classify_pop)
taz2nesting = taz2nesting.set_index('taz_id')

for taz in zero_pop_tazs:
    taz2nesting.loc[taz] = [np.nan, 0, 'No Population', '0']

for i in range(max_bgs):
    taz2nesting['blkgrp_%s'%(i+1)] = np.nan

for taz in taz2nesting.index:
    taz_nesting = taz2nesting.loc[taz, 'nesting_id']
    bgs_in_taz = list(bg2nesting[bg2nesting == taz_nesting].index)
    bgs_in_taz += (max_bgs - len(bgs_in_taz))*[np.nan]
    taz2nesting.loc[taz, ['blkgrp_%s'%(i+1) for i in range(max_bgs)]] = bgs_in_taz

bg2nesting = pd.DataFrame(bg2nesting)
bg2nesting['nesting_id'] = bg2nesting[0]
del bg2nesting[0]
bg2nesting.index.name = 'blkgrp_id'

bg2nesting = bg2nesting.reset_index()
bg2nesting['pop'] = bg2nesting['blkgrp_id'].map(bg_pops)
bg2nesting['nest_type'] = bg2nesting['nesting_id'].map(nestings['type'])
bg2nesting['pop_class'] = bg2nesting['pop'].apply(classify_pop)
bg2nesting = bg2nesting.set_index('blkgrp_id')

for bg in zero_pop_bgs:
    bg2nesting.loc[bg] = [np.nan, 0, 'No Population', '0']

for i in range(max_tazs):
    bg2nesting['TAZ_%s'%(i+1)] = np.nan

for bg in bg2nesting.index:
    bg_nesting = bg2nesting.loc[bg, 'nesting_id']
    tazs_in_bg = list(taz2nesting[taz2nesting['nesting_id'] == bg_nesting].index)
    tazs_in_bg += (max_tazs - len(tazs_in_bg))*[np.nan]
    bg2nesting.loc[bg, ['TAZ_%s'%(i+1) for i in range(max_tazs)]] = tazs_in_bg

del taz2nesting['nesting_id']
del bg2nesting['nesting_id']

print('Writing Output Files')
taz2nesting.sort_index().to_csv(taz2bg_file)
bg2nesting.sort_index().to_csv(bg2taz_file)

print('Go')
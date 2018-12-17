import pandas as pd
import numpy as np
import os

base_path = os.path.split(__file__)[0]
infile = os.path.join(base_path, 'Blk_BG_TAZ_Lookup.csv')
outfile = os.path.join(base_path, 'BG_TAZ_Nesting.xlsx')

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

#The "Share Matrix" (I'm not sure if that's the best name...) has the TAZs as the rows and the block groups as the columns
#It is equal to 1 if the TAZ and the Block Group share population, and 0 if they do not
share_matrix = pop_matrix.astype(bool).astype(int)

tazs_in_bgs = {} #Dictionary listing all of the block groups that intersect with each TAZ
bgs_in_tazs = {} #Dictionary listing all of the TAZs that intersect with each block group

one_taz_in_bgs = {} #Dictionary for block groups that intersect only one TAZ
one_bg_in_tazs = {} #Dictionary for TAZs that intersect only one block group

#######################################################################################################################################################################

print('Identifying One-to-One Relationships')
#Find the TAZs that intersect only one block group
for taz in tazs:
    taz_bgs = list(set(np.array(share_matrix.columns) * share_matrix.loc[taz].values)) #Multiplies the block group labels by the TAZ's row in the share matrix to get the block groups that intersect the TAZ. The list(set()) removes duplicates
    taz_bgs.remove(0) #Every row has a zero, so take it out
    bgs_in_tazs[taz] = taz_bgs
    #If the TAZ has only one block group, add it to the dictionary that has those
    if len(taz_bgs) == 1:
        one_bg_in_tazs[taz] = taz_bgs[0]

#Find the block groups that intersect only one TAZ
for bg in bgs:
    bg_tazs = list(set(np.array(share_matrix.index) * share_matrix[bg].values))
    bg_tazs.remove(0)
    tazs_in_bgs[bg] = bg_tazs
    if len(bg_tazs) == 1:
        one_taz_in_bgs[bg] = bg_tazs[0]

#If a TAZ intersects only one block group and that block group only intersects one TAZ, then we have a one-to-one relationship
one_to_one_pairs = []
for taz in one_bg_in_tazs:
    if one_bg_in_tazs[taz] in one_taz_in_bgs:
        one_to_one_pairs.append((taz, one_bg_in_tazs[taz]))

#Create a data frame for the one-to-one pairs
one2one = pd.DataFrame(columns = ['TAZ', 'BG'])
for i in range(len(one_to_one_pairs)):
    one2one.loc[i] = one_to_one_pairs[i]
one2one = one2one.set_index('TAZ')

#######################################################################################################################################################################

print('Identifying multiple block groups nested in a single TAZ')
single_taz_many_bg = {}
for taz in tazs:
    still_could_be_nesting = True #This is a variable that keeps track of whether or not each TAZ's block groups could all be nested in the TAZ
    for bg in bgs_in_tazs[taz]: #Check each block group that the TAZ intersects
        if still_could_be_nesting: #If the sum of the block group's column in the share matrix is greater than one, then that block group is not nested in the TAZ
            if share_matrix[bg].sum() > 1:
                still_could_be_nesting = False
    if still_could_be_nesting: #If it can still be a nesting after all of the block groups have been checked, then it is one
        if len(bgs_in_tazs[taz]) != 1: #One-to-one relationships are recorded elsewhere
            single_taz_many_bg[taz] = bgs_in_tazs[taz]

#Count the highest number of block groups nested in a TAZ to get the right number of columns for the data frame
most_in_nest = 0
for taz in single_taz_many_bg:
    most_in_nest = max(most_in_nest, len(single_taz_many_bg[taz]))

#Record the results
taz_bgs = pd.DataFrame(index = single_taz_many_bg.keys(), columns = range(most_in_nest))
for taz in single_taz_many_bg:
    for j in range(len(single_taz_many_bg[taz])):
        taz_bgs.loc[taz, j] = single_taz_many_bg[taz][j]
taz_bgs.index.name = 'TAZ'
taz_bgs.columns = ['BG #%s'%(i+1) for i in taz_bgs.columns]

#######################################################################################################################################################################

print('Identifying multiple TAZs nested in a single block group')
single_bg_many_taz = {}
for bg in bgs:
    still_could_be_nesting = True
    for taz in tazs_in_bgs[bg]:
        if still_could_be_nesting:
            if share_matrix.loc[taz].sum() > 1:
                still_could_be_nesting = False
    if still_could_be_nesting: #It is
        if len(tazs_in_bgs[bg]) != 1: #Recorded somewhere else
            single_bg_many_taz[bg] = tazs_in_bgs[bg]

#Count the highest number of TAZs nested in block groups
most_in_nest = 0
for bg in single_bg_many_taz:
    most_in_nest = max(most_in_nest, len(single_bg_many_taz[bg]))

#Record the results
bg_tazs = pd.DataFrame(index = single_bg_many_taz.keys(), columns = range(most_in_nest))
for bg in single_bg_many_taz:
    for j in range(len(single_bg_many_taz[bg])):
        bg_tazs.loc[bg, j] = single_bg_many_taz[bg][j]
bg_tazs.index.name = 'BG'
bg_tazs.columns = ['TAZ #%d'%(i+1) for i in bg_tazs.columns]

#######################################################################################################################################################################

print('Writing File')
writer = pd.ExcelWriter(outfile)
one2one.to_excel(writer, sheet_name = 'One-to-One')
taz_bgs.to_excel(writer, sheet_name = 'One TAZ, Many BGs')
bg_tazs.to_excel(writer, sheet_name = 'One BG, Many TAZs')
writer.save()

print('Done')
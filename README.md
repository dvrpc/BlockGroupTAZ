# BlockGroupTAZ

This tool was created to establish the status of one-to-one and nesting relationships in our current 2010 Block Groups and 2010 TAZs. Establishing this relationship allows a prioritization framework for block group delineation revisions for the US Census Bureau’s 2020 Participant Statistical Areas Program (PSAP). Since TAZs will no longer be a geography reported by the Census Transportation Planning Products (CTPP) in post-2020 releases--but block groups will be a reported geography--we are trying to achieve as much alignment as possible of 2020 block groups with our TAZ geography from our travel model. Determining where one-to-one and one-to-many relationships exist already allows us to focus first on the bigger lift of aligning geographies where block group and TAZ boundaries diverge to a larger degree.

The **Python script** located here in GitHub is available for people who wish to modify the script for their purposes or are comfortable in a Python environment. 

The **Executable file was designed for non-coders** who want to open the file and simply upload an input CSV with your local blocks to get the two outputs. The file, instructions on using it, and a sample input are located here: https://drive.google.com/open?id=1sMZxn-9352uUV1Bc3Ys7_PzJ9e-OLn5L

It’s important to note that this is a tabular procedure, rather than a GIS function--as boundaries for block groups and TAZs do not often have exact matches, but the populations they contain can be exactly the same nonetheless. Block groups and tracts are comprised of the same smaller geographic components: census blocks. A sample input file is provided containing block IDs assigned to their respective block group and TAZ IDs. Population (here 2010 pop is used) allows for the procedures to classify the block groups and TAZs by what kind of relationship they have with each other. The following are the categories found in the “nest_type” field:
* [One TAZ = One Block Group],
* [One TAZ = Many Block Groups],
* [Many TAZs = One Block Group],
* [Many TAZs = Many Block Groups],
* [No Population].

There are two output CSVs that result from the procedure:
* __bg2taz.csv__ - a table that’s joinable to a block group shapefile or other table of block groups that can classify the data into the relationships above
* __taz2bg.csv__ - a table that’s joinable to a TAZ shapefile or other table of TAZs that can classify the data into the relationships above

When joined in a GIS file, the outputs help identify areas that are fairly well-aligned and those that we'll need to take a closer look at. The No Population areas in our TAZs may serve well as special block groups--areas with little to no population but often employment centers that will serve well for CTPP worplace analysis and origin destination flows of commute trips.
![bg_nest_types_leg](https://user-images.githubusercontent.com/27835348/52015174-63938600-24af-11e9-9b43-69574a092905.png)![taz_nest_types_leg](https://user-images.githubusercontent.com/27835348/52015191-70b07500-24af-11e9-93e3-f07c14628654.png)
Beyond the relationship classifications, these tables will sum the population of each record (“pop” field) and indicate in the “pop_class” field whether that population is...
* Above [<600], 
* Below [>3000], 
* or within [600-3000]...

...the population thresholds for standard block groups in the 2020 PSAP criteria. 

Additional fields are provided for identifying the one more many related geographies of the opposite dataset. That is, bg2taz.csv will show unique records of each block group (blkgrp_id) and the numbered TAZ columns (TAZ_1, TAZ_2, ...TAZ_11) on the far right and taz2bg.csv will show unique records of each TAZ (taz_id) and the numbered block group columns (blkgrp_1, blkgrp_2, ...blkgrp_13).

Again, the outputs are population based. Most of the time the shapes can be very similar when a one-to-one match is made, but sometimes they may diverge significantly when one commercial or other non-residential area is included in one, but not the other geography. In the case shown below where a TAZ boundary extends well beyond the block group boundary into a commercial area, we may wind up creating a special block group for the commercial area found only in the TAZ. This would allow for future CTPP workplace data to largely reflect workers in the new special block group with high employment to givegreater clarity of work destination locations. 
![one-to-one bg2taz](https://user-images.githubusercontent.com/27835348/52025746-88015980-24d3-11e9-9fc2-334b55f0da1b.png)

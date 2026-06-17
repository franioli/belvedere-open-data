Introduction

This dataset contains extensive, long-term monitoring data on the Belvedere Glacier, a debris-covered glacier located on the east face of Monte Rosa in the Anzasca Valley of the Italian Alps. The data is derived from photogrammetric 3D reconstruction of the full Belvedere Glacier and includes:

dense point clouds obtained with UAV SfM-MVS covering the entire glacier body
high-resolution orthophotos
high-resolution DEMs

Since 2015, in-situ surveys of the glacier have been conducted annually using fixed-wing UAVs until 2020 and quadcopters from 2021 to 2022 to remotely sense the glacier and build high-resolution photogrammetric models. A set of ground control points (GCPs) were materialized all over the glacier area, both inside the glacier and along the moraines, and surveyed (nearly-) yearly with topographic-grade GNSS receivers (Ioli et al., 2022).

For the period from 1977 to 2001, historical analog images, digitalized with photogrammetric scanners and acquired from aerial platforms, were used in combination with GCPs obtained from recent photogrammetric models (De Gaetani et al., 2021).

Before downloading them, you can explore the photogrammetric point clouds of the Belvedere Glacier within a web app based on Potree from https://thebelvedereglacier.it/ (use a web browser from a desktop/laptop for the best experience). Additionally, from here you can also visualize and download the coordinates of the GCPs measured by GNSS every year since 2015.



Data organization

All files are uploaded individually to the repository (replacing the former yearly ZIP archives available in the previous dataset releases).

Data are grouped by survey year. For each survey, the following files are provided:

Metadata is provided as a .json file for each survey year, which contains all the main information for data usage, including the reference system, accuracy statistics, acquisition parameters, and bounding box. 
Point clouds are provided in compressed LAZ format and are distributed as Cloud Optimized Point Clouds (COPC), a spatially indexed variant of LAZ 1.4 that is fully backward compatible. COPC files can be opened in CloudCompare with no difference from a standard LAZ file. In addition, COPC files can be visualized directly in Eptium with a simple drag-and-drop workflow for fast web-based visualization.
Orthophotos and DEMs are georeferenced images (.tif) that can be inspected with any GIS software (e.g., QGIS).

All the files are named according to the following naming schema:

"belv_YYYY_surveyplatform_datatype[_resolution][_vertical_datum][_other].extension"

where: 

YYYY: is the year of the survey
surveyplatform: can be either "uav" for the UAV-based photogrammetry survey, "histo-aerial" for the historical aerial surveys (up to 2002) or "digital-aerial" for recent aerial surveys (2009).
datatype: can be either "pcd" for point clouds, "orthophoto" for orthophotos, or "dsm" for DSMs. 
resolution: on-ground resolution of each pixel in meters. This applies only to raster data (orthophotos and DSMs)
vertical_datum: if the DSM is given in orthometric coordinates, the label "ortho" is present in the filename; otherwise, the height of the dataset is supposed to be ellipsoidal.
Other metadata can be added at the end of the filename (e.g., "cocp" that stands for Cloud Optimized Point Clouds format for point clouds).



Data Usage

This dataset can be used to estimate glacier velocities, volume variations, study geomorphological processes such as the process of moraine collapse, or derive other information on glacier dynamics. If you have any requests on the data provided, data acquisition, or the raw data themselves, you are encouraged to contact us.



Contributions

The monitoring activity carried out on the Belvedere Glacier was designed and conducted jointly by the Department of Civil and Environmental Engineering (DICA) of Politecnico di Milano and the Department of Environment, Land and Infrastructure Engineering (DIATI) of Politecnico di Torino. The DREAM projects (DRone tEchnnology for wAter resources and hydrologic hazard Monitoring), involving teachers and students from Alta Scuola Politecnica (ASP) of Politecnico di Torino and Milano, contributed to the campaign from 2015 to 2017.



Acknowledgements

The authors thank CGR SpA for digitizing the historical images (1977, 1991, 2001, 2009) and making them available to the authors for the photogrammetric processing.
The authors thank all students and collaborators contributing to the Alta Scuola Politecnica projects DREAM 1, DREAM 2, and DREAM 3 (DRone tEchnnology for wAter resources and hydrologic hazard Monitoring). 



If you use the data, please, cite these our pubblications:

Open data description, monitoring project, and recent data acquisition strategy: Gaspari, F., Barbieri, F., Fascia, R., Ioli, F., Pinto, L., & Migliaccio, F. (2025). Strategies for Glacier Retreat Communication with 3D Geovisualization and Open Data Sharing. ISPRS International Journal of Geo-Information, 14(2), 75. https://doi.org/10.3390/ijgi14020075
UAV datasets: Ioli, F.; Bianchi, A.; Cina, A.; De Michele, C.; Maschio, P.; Passoni, D.; Pinto, L. Mid-Term Monitoring of Glacier’s Variations with UAVs: The Example of the Belvedere Glacier. Remote Sensing, 14, 28 (2022). https://doi.org/10.3390/rs14010028
Historical aerial datasets: De Gaetani, C.I.; Ioli, F.; Pinto, L. Aerial and UAV Images for Photogrammetric Analysis of Belvedere Glacier Evolution in the Period 1977–2019. Remote Sensing, 13, 3787 (2021). https://doi.org/10.3390/rs13183787
Short-term Belvedere monitoring: Ioli, F., Dematteis, N., Giordan, D., Nex, F., Pinto, L., Deep Learning Low-cost Photogrammetry for 4D Short-term Glacier Dynamics Monitoring. PFG (2024). https://doi.org/10.1007/s41064-023-00272-w
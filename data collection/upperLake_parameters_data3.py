import ee
import pandas as pd

# Initialize Earth Engine
ee.Initialize()

# Define the AOI (Area of Interest) using coordinates
aoi = ee.Geometry.Rectangle([-122.44, 37.74, -122.39, 37.8])

# Define the Cloud Mask function to remove clouds from the images
def maskClouds(image):
    qa = image.select('QA60')
    cloud = qa.bitwiseAnd(1 << 10).eq(0)
    return image.updateMask(cloud)

# Define the NDWI function to identify water bodies
def ndwi(image):
    return image.normalizedDifference(['B3', 'B8'])

# Load the Sentinel-2 image collection for the defined AOI and date range
collection = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterDate('2021-01-01', '2023-01-31') \
    .filterBounds(aoi)

# Apply the Cloud Mask function to the image collection
collection = collection.map(maskClouds)

# Get the dates of the images in the collection
dates = collection.aggregate_array('system:time_start').getInfo()

# Create an empty list to store the results
results = []

# Loop through each date in the list
for date in dates:
    
    # Load the image for the current date
    image = ee.Image(collection.filterMetadata('system:time_start', 'equals', date).first())
    
    # Apply the NDWI function to the image
    ndwi_image = ndwi(image)
    
    # Create a binary mask for water bodies using the NDWI threshold of 0.4
    water_mask = ndwi_image.gt(0.4)
    
    # Calculate the mean temperature and chlorophyll values for the water bodies
    temperature = image.select('B11').mask(water_mask).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=10
    ).getInfo()
    chlorophyll = image.select('B2').mask(water_mask).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=10
    ).getInfo()
    
    # Add the results to the list
    results.append({
        'date': date,
        'temperature': temperature.get('B11'),
        'chlorophyll': chlorophyll.get('B2')
    })

# Convert the results to a Pandas dataframe
results_df = pd.DataFrame(results)

# Save the results to a CSV file
results_df.to_csv('daily_water_properties.csv', index=False)

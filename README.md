# abergavenny_prices

some kind of spatial model most likely a GAM. Allowing me to get back into spatial data manipulation and especially to get more time hands on with geopandas package as other than using it briefly or choropleth maps ive not really touched it. the plan is to use the whole local area not sure where we'll find our limits.

so far the data sources i plan to use are:

https://landregistry.data.gov.uk/app/ppd <- for historic prices for each property in the area
https://www.doogal.co.uk/BatchGeocoding.php <- for long lat values per postcode in batch

need to find some peripheral datasets too to supplement these data i.e. distance from major conveniences / landmarks, number of bedrooms if possible, maybe even plot size for the house. hopefully we can do a combination of data vis and general dicking around here...

current progress:
    - brought those two datasets together
    - setup initial analysis dashboard with basically 0 features
Up next:
    - further cleaning / feature engineering
    - track down peripheral datasets
    - add new graphs to dashboard



<b><font size = '6'>OpenStreetMap Data Project</font></b>
<br><br>
<font size = '3'>Siddharth Kumar</font>

<b><font size = '5'> Map Area </font></b>
<br>
<font size = '3'> Columbus, Ohio, USA </font>
<br>
<ul>
    <li>https://www.openstreetmap.org/relation/182706#map=11/39.9511/-82.9176</li>
</ul>
<br>
This area is of the city where I went to college. While I'm already familiar with campus area and downtown Columbus, I chose this map to learn more about surrounding areas and less popular spots. I also used my previous knowledge of the area to check the validity of the dataset.

<b><font size = '5'> Problems Encountered in Map </font></b>

<b><font size = '4'> Keys: </font> </b>
<ul>
    <li><b> Repetitive/Similar Key Names</b></li>
    When keys had similar names, I changed them to the more common one.
    <br>
    <i> ex: ('County', 'county_name'), ('ST_num', 'state_id'), ('url, website') </i>
    <li><b> Nested Tag Type </b></li>
    For keys that started with a word followed by a ':', I set the first word to the 'type' attribute for all tags
    <br>
    <i> ex: 'addr:street', 'contact:phone', 'surveillance:webcam' </i>
    <li><b> Nested Naming Authority </b></li>
    If the type attribute was 'tiger' or 'gnis', I set it to an attribute called 'naming_auth' (Naming Authority). The 'Geographic Names Information System' (GNIS) contains information on geographic features in the US, and 'Topologically Integrated Geographic Encoding and Referencing' (TIGER) is used by the US Census to describe land attributes. Both these naming authorites have integrated their data with OSM.
    <br>
    <i> ex: 'tiger:county', 'tiger:zip_right', 'gnis:state_id' </i>
</ul>
<br>
<b><font size = '4'> Values: </font></b>
<ul>
    <li><b> Unstandardized Values: </b></li>
    All unstandardized values were converted to standard formats. Unstandardized values were most likely due to different naming conventions used by GNIS and TIGER, as well as human input. I did not see any problems related to location specific formatting. Most formats, such as 9 digit postal codes and (555) 555-5555 phone number style were easily recognizable and easy to fix. <br><br>
        <ul>
        <li><b> Street Names </b></li>
        <i> unstandard: 'W. Woodruff Ave', 'National Road SW' 
        <br> standard: 'West Woodruff Avenue', 'National Road Southwest' </i>
        
        <li><b> State Names </b></li>
        <i> unstandard: 'OH', 'OH - Ohio'
        <br> standard: 'Ohio' </i>
        
        <li><b> City Names </b></li>
        <i> unstandard: 'Columbus, OH', 'Columbus, Ohio', 'columbus'
        <br> standard: 'Columbus' </i>
        
        <li><b> County Names </b></li>
        <i> unstandard: 'OH:Franklin'
        <br> standard: 'Franklin' </i>
        
        <li><b> Postcodes </b></li>
        <i> unstandard: '43201-3247', 'OH 43201', '4320'
        <br> standard: '43201' </i>
        
        <li><b> Phone Numbers </b></li>
        <i> unstandard: '(614) 555-5555', '614-555-5555', '+1 (614) 555-5555'
        <br> standard: '6145555555', '16145555555' </i>
        
        <li><b> Speed Limits </b></li>
        <i> unstandard: '55'
        <br> standard: '55 mph' </i>
        
        <li><b> Restaurant Cuisines </b></li>
        <i> unstandard: 'ice cream', 'Ice_Cream'
        <br> standard: 'ice_cream' </i>
   </ul>
   
   <li><b> Nested Values in Same String </b></li>
   Values that contained multiple nested values were separated and treated as individual tags.
   <br>
   <i> ex: 'bar;restaurant', '43201:43210', 'Franklin, Licking, Delaware' </i>
</ul>
   
        
    
    

<b> <font size = '4'> Separating Nested Values </font></b>
<p>I dealt with nested values by assuming that all values had multiple nested values. By calling the ```process_value``` method for each value, I split the value by its delimeter and returned a list of values. A tag was created for each value in the returned list. Most of the time, the list only contained one value, therefore only one tag was created.</p>

```python
def process_value(key, value):
    split_symbols = [';', ',_', ',', ':', '_/_']
    split_vals = list()

    if key in ['ref', 'county', 'destination', 'phone', 'exit_to', 'cuisine', 'amenity'] or key.startswith('zip'):
        for symbol in split_symbols:
            if symbol in value:
                for item in value.split(symbol):
                    split_vals.append(item.strip())
                break
        if len(split_vals) == 0:
            split_vals.append(value)
    else:
         split_vals.append(value)
    return split_vals
```

<b><font size = '4'> Nodes Tags Defined as Ways Tags </font></b>
<p> While auditing street names in ways tags, I noticed obscure street names such as <i> 'CVS Pharmacy', 'Riverside Methodist Hospital', 'Huber Ridge Elementary School'</i>, and many others. Knowing that these did not belong as way tags, I programatically removed them. I accomplished this with the ```is_valid_way_element``` method. It basically checked to see if the element contained keys like 'building', 'leisure', and 'shop'. If it did, I assumed that the tag was not describing what a way tag is supposed to be, and returned ```False```. Before appending the first level element, I ran this method to ascertain its validity as a way tag.

```python
def is_valid_way_element(tags):
    unwanted_way_keys = ['building', 'leisure', 'shop', 'amenity', 'tourism', 'landuse', 'housename']
    for way_tag in tags:
        if (way_tag['key'] in unwanted_way_keys) or (way_tag['type']=='addr'):
            return False
    return True
```

<b><font size = '4'> Auditing ZipCode Accuracy </font></b>
<p> After auditing data validity in Python, I was curious to test accuracy using gold standard data. I figured zipcode data would be a good place to start. I downloaded a list of zipcodes in the US from aggdata.com. The original source of the data is from geonames.org, a free geographical database. I ran a query that compared city names from OSM and GeoNames, matching on zipcode. Most cities were the same, so I only displayed those that were not.
</p>

```mysql
sqlite> SELECT a.value AS zip, b.value AS osm_city, c.city AS geonames_city
   ...> FROM nodes_tags a, nodes_tags b
   ...> LEFT JOIN zip_codes c
   ...> ON zip = c.zipcode
   ...> WHERE a.id = b.id
   ...> AND a.key = 'postcode'
   ...> AND b.key = 'city'
   ...> AND (osm_city != geonames_city OR geonames_city IS NULL)
   ...> GROUP BY zip, osm_city;
```

```
| zip   | osm_city          | geonames_city | 
|-------|-------------------|---------------| 
| 43081 | Columbus          | Westerville   | 
| 43085 | Worthington       | Columbus      | 
| 43207 | Obetz             | Columbus      | 
| 43209 | Bexley            | Columbus      | 
| 43212 | Grandview Heights | Columbus      | 
| 43213 | Grove City        | Columbus      | 
| 43213 | Whitehall         | Columbus      | 
| 43220 | Upper Arlington   | Columbus      | 
| 43221 | Upper Arlington   | Columbus      | 
| 43230 | Gahanna           | Columbus      | 
| 43328 | Columbus          |               | 
```


I checked the validity of this table by searching the zipcodes on usps.com and found that many of the OSM cities were listed as "recognized" cities under that zipcode, however not the default. The GeoNames data matched all zipcodes to their default city. Two cases where OSM data is wrong are 43081 and 43328. According to usps.com, 43081 is only used for Westerville, OH and 43328 is not valid. These are confirmed in the GeoNames data. As a result, I updated the database to show only the GeoNames cities and removed the invalid zipcode.

<b><font size = '5'> Overview of the Data </font></b>

<b><font size = '4'> File Sizes </font></b>
<ul>
    <li> ColumbusOhio.osm -- 82 MB </li>
    <li> columbus_osm.db -- 44 MB </li>
    <li> nodes.csv -- 30 MB </li>
    <li> nodes_tags.csv -- 0.95 MB </li>
    <li> ways.csv -- 1.9 MB </li>
    <li> ways_tags.csv -- 7.7 MB </li>
    <li> ways_nodes.csv -- 6.5 MB </li>
    <li> us_postal_codes.csv -- 2.3 MB </li>
</ul>

<b><font size = '4'> Number of Unique Users </font></b>
```mysql
sqlite> SELECT COUNT(nodes_and_ways.uid)
   ...> FROM (SELECT uid FROM nodes
   ...>       UNION
   ...>       SELECT uid FROM ways
   ...>       GROUP BY uid) nodes_and_ways;
```

<font size = '3'> 514 </font>

<b><font size = '4'> Number of Nodes </font></b>
```mysql
sqlite> SELECT COUNT(*) FROM nodes;
```
<font size = '3'> 375132 </font>

<b><font size = '4'> Number of Ways </font></b>
```mysql
sqlite> SELECT COUNT(*) FROM ways;
```
<font size = '3'> 33331 </font>

<b><font size = '4'> Top 10 Cuisines </font></b>
<p> As someone who loves to eat, I'm curious to see what the most popular cuisine is in Columbus. </p>
```mysql
sqlite> SELECT value, COUNT(value)
   ...> FROM nodes_tags
   ...> WHERE key = 'cuisine'
   ...> GROUP BY value
   ...> ORDER BY COUNT(value) DESC
   ...> LIMIT 10;
```

```
| cuisine     | count | 
|-------------|-------| 
| mexican     | 20    | 
| pizza       | 20    | 
| american    | 19    | 
| burger      | 19    | 
| sandwich    | 19    | 
| coffee_shop | 16    | 
| italian     | 14    | 
| chinese     | 12    | 
| asian       | 9     | 
| ice_cream   | 9     | 
```

<b><font size = '4'> Streets With Pizza </font></b>
<p> In the last query, I found that 'mexican' and 'pizza' are the 2 most popular cuisines. As a result, I decided to find out what streets had the most options for pizza. </p>

```mysql
sqlite> SELECT a.value, COUNT(a.value)
   ...> FROM nodes_tags a, nodes_tags b
   ...> WHERE a.id = b.id
   ...> AND a.key = 'street'
   ...> AND b.key = 'cuisine'
   ...> AND b.value = 'pizza'
   ...> GROUP BY a.value
   ...> ORDER BY COUNT(a.value) DESC;
```

```
| street            | count | 
|-------------------|-------| 
| North High Street | 5     | 
| Indianola Avenue  | 1     | 
| South High Street | 1     | 
| West Fifth Avenue | 1     | 
| West Lane Avenue  | 1     | 
```

<b><font size = '4'> Pizza Places on North High Street </font></b>

<p> According to the last query, North High Street had the most pizza places than any other street in Columbus. My last step was to find the names of these places, and make my final lunch decision! </p>

```mysql
sqlite> SELECT a.value
   ...> FROM nodes_tags a, nodes_tags b, nodes_tags c
   ...> WHERE a.id = b.id
   ...> AND b.id = c.id
   ...> AND a.key = 'name'
   ...> AND b.key = 'street'
   ...> AND b.value = 'North High Street'
   ...> AND c.key = 'cuisine'
   ...> AND c.value = 'pizza';
```
```
| name              | 
|-------------------| 
| Hound Dog's Pizza | 
| Papa John's       | 
| Cottage Inn Pizza | 
| Anges Pizza       | 
| Blaze Pizza       | 
```

<b><font size = '5'> Ideas For Improving the Dataset </font></b>

When analyzing the data in Python, I found that there were multiple instances of node data listed as ways. I originally thought of converting these invalid ways to nodes, however I found it to be impossible due to the different conventions used for nodes and ways. (<i>eg: nodes require latitude and longitude data, while ways do not</i>) As a result, I had to remove all of these invalid ways programmatically. Since there was a lot of valuable node information being removed, I would suggest a way for OSM to safeguard against careless user entry. I was able to discern valid ways from invalid ways by checking its key values. Generally, if ways had key names like 'leisure', 'shop', or 'building', it was safe to assume that it wasn't actually a way. Perhaps OSM can check key names before adding them to their dataset? If this were implemented, it would ensure that valuable node data isn't wasted. However, A drawback of checking way information programmatically is that it may prevent users from entering valid way data.

<b><font size = '5'> Conclusion </font></b>
<p> While this OSM dataset is nowhere near complete, it's a good start toward providing developers a free, open source method of mapping the world. I liked the idea of integrating TIGER data into the map; if OSM were able to integrate with more GPS mapping services (<i>i.e. Garmin, TomTom, etc.</i>), it could build a much more informative and accurate datset. 

<b> Resources Used -- N/A </b>
```python

```

# PolitiTracker Design Components

## APIs

This project depended on extensive use of APIs to retrieve unique information about congressional representatives given just an address. The problem was, I didn't have any clue what an API was or how to use it, so it took a significant amount of Googling, YouTube-watching, and Stack Exchange-browsing to fully understand them. While the actual lines that call the APIs and store their information are small, they represent the culmination of hours of research into each API to discover how they stored the relevant information.

Finding and figuring out how to access the APIs was by far my biggest hurdle in this project and made up the lions-share of my time. Each API represented info in different ways, and often the API didn't display the info in a way that suited my purposes (as was the case for the OpenSecrets API and my "funding" page). In these situations, I had to devise ways to access the APIs with Python code and retrieve the info in a roundabout way.

I used a few main APIs in this project:

* Google Civics API - to turn the address into a state and a district
* ProPublica API - to get general biographical info as well as voting history
* OpenSecrets API - to get funding history
* The United States Project API - to retrieve photos of representatives
* The Twitter API - to retrieve a representative's recent tweets

I decided to query APIs, as opposed to downloading the information and storing it on the server, because the APIs were updated regularly. Although this costs me some speed in loading pages, I would rather the information be up-to-date than load at lightning speeds.

## Storing user information

Although I initially considered creating a login and personal accounts to access the website, I eventually decided against it due to the lack of unique information that was being stored and to just increase overall accessibility.

Instead, I decided to use the session dictionary to store relevant information when the user moved from page to page. I created a @location_required function that made the other sections of the page, such as /media or /funding "off-limits" if the user hadn't inputted their address. Once an address was inputted, I made a request to the Google Civics API and stored the corresponding state and congressional district in a session attribute. I also stored other information in the session attribute that would need to be accessed later on other pages. The session attribute was cleared each time the user clicked "Reset Location".

## Website Design

I used Bootstrap's NavBar because it was the best option, but I changed the color scheme and fonts to personalize it a bit more. Additionally, I show the user two different NavBard displays depending on whether they have entered their address. If they haven't yet entered it, I only display the "Set Location" tab. If they have entered it, then I switch to the other view that has all of the normal tabs (funding, votes, etc.).

On the homepage, I retrieved a standard photo of the representative from the United States Project API and set the background to be blue or red depending on the representative's party. I also used Bootstrap "cards" to display information in a more visually-appealing, modern way. Finally, I used a service by GovTrack to embed an iframe outlining the given district on a map.

For the votes and funding pages, I used Jinja to dynamically render tables representing the data. I also added some JavaScript functionality using code built by datatables.net to allow each column of the table to be sorted.



## Deviations From My Initial Project Proposal

Although I started out believing I would make a site for both senators and representatives, I decided not to include senators because I wanted
the focus of the site to be on districts and their representatives. Senators receive more publicity already, and representatives are often less well-known. If I decide that I want to include senators down the road, I would only need to add a few more lines of code to make it happen.
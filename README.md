# BTDY Scraper Django Web App

This purpose of this project is to create a front end for admins of the BTDY iRacing league to be able to enter in subsession id's from recent races and have the points automatically calculate for that given race. This webapp utilizes the Django framework to create the front end website and backend processes. There is custom scripts to pull data from [iracing.com](https://www.iracing.com) utilizing their API. After pulled the data is manipulated and stored in a backend MariaDB database.

The web app and data base are hosted locally and can be found here, URL is subject to change depending on if I want to purchase a new one:

[points.tbandj.net](https://points.tbandj.net)

### User View Screen Shots

#### Home Page
The home page gives the overall season standings so far, and a list of completed race sessions to the right.
![contender-home](https://user-images.githubusercontent.com/28052084/175173607-0bc63344-4e68-4062-9956-53a17bda569a.png)

#### Penalty Report Page
The penalty report page displays any penalties that have been given to drives across all races.
![penalty-page](https://user-images.githubusercontent.com/28052084/175174581-8a9c4b8d-07a0-416f-94ce-c28421cc46c4.png)

#### Race Session Results
These pages display the results for any given race throughout the season.
![image](https://user-images.githubusercontent.com/28052084/175178569-8e0d99a8-6cdf-4033-84d9-ba532f50762b.png)

## Features

1. Admin Logins
   
   League admins can create accounts to be able to process new races, add penalties, adjust bonuses and so on.

   ![image](https://user-images.githubusercontent.com/28052084/175175941-5ad3dabc-a0a7-4942-9053-a7573510797b.png)

2. iRacing API data pulls

   The Add a Race form takes in the Subsession ID of the race, round number, bonus, series, and season. The web app will connect to iracings API to pull the data for that race and perform the points calculations for that race. The bonus for that race (Least Incidents, Fastest Lap Average, or Pole Position) will also be applied for that particular race. All of the information is then stored in a backend database to be used throughout the app.

   ![image](https://user-images.githubusercontent.com/28052084/175177218-ea23d918-e991-4780-9966-cb021b147bbf.png)

   There are also checks in place to catch for bad subsession IDs, duplicate subsession IDs in the database, and BTDY Contender specific subsessionIDs

   ![image](https://user-images.githubusercontent.com/28052084/175179285-e0045685-a170-4583-aca3-ec9c68606611.png)

   ![image](https://user-images.githubusercontent.com/28052084/175179225-863f0627-28a9-4b6b-9848-bc467518df67.png)

   ![image](https://user-images.githubusercontent.com/28052084/175179346-0f92ae91-5eaa-4c18-836b-8bd2fd724175.png)

3. Modfiying individual driver results
   
   You can modify individual driver results per race session. You can change things like the total points gained that race, their total bonus dollar amount, issue them a penalty and add penalty notes, or add in any additional bonus notes. Issuing a penalty and adding notes will automatically populate on the Penalty Report page.

   ![image](https://user-images.githubusercontent.com/28052084/175178212-dcd007eb-f037-4b24-9178-43b66ac42dde.png)

4. Deleting Race Sessions and Individual Driver Records

   Options to delete an entire race sessions, or an individual driver from a specific race. Use case for this is if someone joins a session but turns no laps.

   ![image](https://user-images.githubusercontent.com/28052084/175177507-5ebcbe5c-2b4b-44a0-94e5-bfef9d480f62.png)

   ![image](https://user-images.githubusercontent.com/28052084/175177658-51639571-5d75-461b-9c69-4c591193f00d.png)

   Prior to submitting any delete request a model will pop up asking for confirmation.

   ![image](https://user-images.githubusercontent.com/28052084/175177766-b12eaa21-d3f0-4429-bc7f-8ad5857162f3.png)

## Planned Features

1. Admin Panel allowing you adjust points distribution and payout amounts all from the front of the web app. For ex:
   * Starting points at 40 instead of 43
   * Decreasing by 2 points per position finished instead of 1
   * Changing bonus payout amounts

2. Add in season/career stats page for drivers across the Contender Series
3. Expand to include Premier Series
4. Expand to include other leagues

If there are other thoughts on features to add, please let me know.
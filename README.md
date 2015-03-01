**Get hours-worked vs. estimated points for your tracker stories.**




1. Get [your Tracker API token](https://www.pivotaltracker.com/profile)

2. Get a project ID, the number at the end of your project page URL

3. Install dependencies
  ```bash
  pip install --upgrade pytz requests
  ```

4. Run it:
  ```bash
  ./stats.py $API_TOKEN $PROJECT_ID
  ```

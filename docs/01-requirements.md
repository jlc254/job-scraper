To test your job boards one by one, the best way is to use the run command in the CLI with the --sources flag. This allows you to isolate a single adapter and verify its output without running the entire pipeline.
1. Find your Source IDs
First, you need to know the exact IDs of the job boards you have configured. These are defined in your config/sources.yaml file.
To see all available source IDs, run:
cat config/sources.yaml
(Look for the top-level keys in that file, e.g., himalayas, jobicy, linkedin, etc.)
2. Run a Single Source
Once you have the ID, use the following command:
python main.py run --sources <source_id>
Example (if you want to test just "himalayas"):
python main.py run --sources himalayas
3. How to Verify the Data
Depending on your storage setup, here is how to check if the data was fetched correctly:
A. Check the Console Output
The scraper usually prints progress logs to the terminal. Look for:
- Fetching jobs from...
- Found X jobs
- Stored Y new jobs
- Any ERROR or WARNING logs during the fetch.
B. Check the Storage (Google Sheets)
If you are using Google Sheets, open your sheet. Since you are running only one source, you should see new rows appearing specifically for that board.
C. Check the Local Database (SQLite)
If you are using SQLite (or want to check the local cache), you can query the database:
sqlite3 output/jobs.db "SELECT * FROM jobs WHERE source_id = 'himalayas' LIMIT 5;"
D. Use "Dry Run" for Fast Testing
If you don't want to write to your database or sheets every time you test, use the --dry-run flag. This will fetch the data and print it (or process it) without saving it permanently:
python main.py run --sources himalayas --dry-run
Summary Checklist for Testing a Board:
1. Command: python main.py run --sources <id> --dry-run
2. Watch for: Found X jobs in the logs.
3. Verify: Check if the job titles, companies, and links look correct in the output/logs.


$ python main.py run --sources himalayas --no-notify

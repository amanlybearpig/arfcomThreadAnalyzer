# arfcomThreadAnalyzer
Analyze arfcom thread and save to db

To use, either:
1) run from cmd line: python downloadArfcomThread.py \<link to thread> \<optional database name>
2) import and run ArfcomThread.download(\<link to thread>, \<optional databaseName>)

It will download the thread and extract posts and save to an sqlite database in the run directory. Each post has an author, a date, an id, and a time. It will by default list the top 10 posters in the thread and their number of posts, and plot posts per day. Other post-processing can be done as well using pandas or some other data analysis tool.

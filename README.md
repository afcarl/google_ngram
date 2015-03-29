# GoogleNGram downloader (Python 2.7 and 3, Mechanize)
## Karl Stratos (stratos@cs.columbia.edu)
This is a set of scripts that help download Google NGram files from the web.

1. Install the mechanize package. I used the command:

   `sudo easy_install mechanize`

2. Create a file of URLs. E.g., to get all English 5-gram files, type:

   `mkdir eng-5gram`

   `python scripts/collect_file_urls.py googlebooks-eng-all-5gram-20120701-\(.*\).gz eng-5gram/urls.txt`

3. Download the files at the URLs using wget -i:

   `wget -i eng-5gram/urls.txt -P eng-5gram/`

4. Create a processed file of actual n-gram counts in the downloaded files:

   `python3 scripts/merge_files.py eng-5gram eng-5gram.txt`
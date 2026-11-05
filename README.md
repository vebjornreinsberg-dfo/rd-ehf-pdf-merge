Before running this program:
Create a local C:\\Temp\\EHF\\
Into that directory, add one or more EHF files (XML)

Then build (with docker-compose.yml)
docker compose build

Then run (with docker-compose.yml
docker compose run --rm ehf-pdf-merge

You will now get new/ converted file(s) in your local directory C:\\Temp\\EHF\\converted

You can also run with parameter, if you want to also generate the merged PDF as a file
docker compose run --rm ehf-pdf-merge --save-merged-pdf

If the XML file contains only one attachment, as Commercial Invoice, nothing is done with the file content
If the XML file contains more than one attachment, all are merged into one, and the Base64 string of this new file will replace the original Commercial Invoice. The other attachments are removed.


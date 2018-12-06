PYTHON = python3.exe
MAIN_SCRIPT = allchan.py
CONFIG = allchan.json

SQLITE3 = sqlite3.exe
DB = allchan.sqlite3

EDITOR = "C:\Program Files\Notepad++\notepad++.exe"

all: update sync query

watch:
	$(PYTHON) $(MAIN_SCRIPT)

sync:
	$(PYTHON) $(MAIN_SCRIPT) -sync

update:
	$(PYTHON) $(MAIN_SCRIPT) -update

conf:
	$(EDITOR) $(CONFIG)

clean:
	rm -rf *.log

sql:
	$(SQLITE3) $(DB)

backup:
	cp $(DB) $(DB).bak

query:
	$(SQLITE3) $(DB) "SELECT COUNT(*) FROM Image GROUP BY status;"

JOBMANGO_ZIP=jobmango.zip
JOBMANGO_DEST=jobmango

usage:
	@echo make jobmango_zip or
	@echo make jobmango_install

jobmango_zip:
	zip -r ${JOBMANGO_ZIP} Makefile jobmango.py config.ini fish iqueue oqueue equeue mom
	
jobmango_install:
	mkdir ${JOBMANGO_DEST}
	unzip ${JOBMANGO_ZIP} -d ${JOBMANGO_DEST}

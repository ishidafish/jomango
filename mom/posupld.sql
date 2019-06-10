/* DA_POSUPLD_SQL.PROCESS_ITEM :
http://127.0.0.1/rest/do.php?action=[
{"sql":"posupld",
"type":"execute",
"rows":[
{"commit":"Y","ITEM":"1014303091143220","LOC":"1001000189","TRAN_DATE":"2018-04-01","SALE_QTY":"-10","SALE_AMT":"80"},
{"commit":"Y","ITEM":"1014303091143225","LOC":"1001000189","TRAN_DATE":"2018-04-01","SALE_QTY":"-11","SALE_AMT":"90"}
]}]
*/
DECLARE
    execute_status Boolean;
BEGIN 
    execute_status := DA_POSUPLD_SQL.PROCESS_ITEM(
        :ERROR_MESSAGE,
        :ITEM,
        :LOC,
        TO_date(:TRAN_DATE,'YYYY-MM-DD');
        :SALE_QTY,
        :SALE_AMT);
exception
    When OTHERS THEN
        :ERR_MESSAGE := sqlerrm;
END;
  
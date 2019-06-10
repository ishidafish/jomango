/* test */
declare
  procedure a(i in out number) is 
  begin 
	i := sqrt(i) ; 
  end;
begin
  a(:num);
  :num := :num +:num1;
  :num1 :='我是一片云';
end;
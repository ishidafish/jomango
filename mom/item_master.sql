 select item,item_desc 
   from item_master 
  where item like :item||'%' and rownum<=100
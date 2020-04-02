
function toDatetime(date_str) {
  try {
    var day = +date_str.substring(0,2);
    var month = +date_str.substring(3,5);
    var year = +date_str.substring(6, 10);

    if ((month > 12) || (month < 0) || (day < 0) || (day > 31)) {
      return false; 
      
    } else {
      var date_iso = year + "-"+ month + "-" +day + "T00:00:00-0000";
      var date_ = new Date(date_iso);
      return date_
    }
  } catch (error) {
   return false; 
  }
}

function restrictDate(dateObj) {
  // Make sure the date is within the possible range:
  // first : November 2019
  // last  : today
  try {
    var firstDate = new Date('2019-11-01T00:00:00-0000').valueOf();
    var now = new Date().valueOf();
    var date_utc = dateObj.valueOf();
    
    if ((date_utc > now) || (date_utc < firstDate)){
      return false;  
    } else {
      return true;
    }
  } catch (error) {
   return false; 
  }
}

function dateValidation() {
  var Cell = SpreadsheetApp.getCurrentCell()
  var date = Cell.getValue();
  
  if (date == '') {
    return true
  }

  var status = true
  
  // Accepted Date patterns. 
  var rx1 = /^\d{2}\.\d{2}\.\d{4}$/;
  var rx2 = /^- \d{2}\.\d{2}\.\d{4}$/;
  var rx3 = /^\d{2}\.\d{2}\.\d{4} -$/;
  var rx4 = /^\d{2}\.\d{2}\.\d{4} - \d{2}\.\d{2}\.\d{4}$/;
  
  var test1 = date.match(rx1);
  var test2 = date.match(rx2);
  var test3 = date.match(rx3);
  var test4 = date.match(rx4);
  
  if(test1) {
   var dateObj = toDatetime(date);
   status = restrictDate(dateObj);
    
  } else if (test2) {
    var dateObj = date.substring(2,12);
    status = restrictDate(dateObj);
    
  } else if (test3) {
    var dateObj = date.substring(0,10);
    status = restrictDate(dateObj);
    
  } else if (test4){
    dateObj1 = toDatetime(date.substring(0,10));
    dateObj2 = toDatetime(date.substring(13, 23));
    status = restrictDate(dateObj1);
    status = restrictDate(dateObj2);
    
    var date1_utc = dateObj1.valueOf();
    var date2_utc = dateObj2.valueOf();
    if (date1_utc >= date2_utc){
     status = false;
    }
  } else{
    status = false;
  }
  return status;
}



function dateCheck(date) {
    var status = false;
  
    // Accepted Date patterns. 
    var rx1 = /^\d{2}\.\d{2}\.\d{4}$/;
    var rx2 = /^- \d{2}\.\d{2}\.\d{4}$/;
    var rx3 = /^\d{2}\.\d{2}\.\d{4} -$/;
    var rx4 = /^\d{2}\.\d{2}\.\d{4} - \d{2}\.\d{2}\.\d{4}$/;
    
    var test1 = date.match(rx1);
    var test2 = date.match(rx2);
    var test3 = date.match(rx3);
    var test4 = date.match(rx4);
    
    if(test1) {
      var dateObj = toDatetime(date);
      status = restrictDate(dateObj);
      
    } else if (test2) {
      var dateObj = date.substring(2,12);
      status = restrictDate(dateObj);
      
      
    } else if (test3) {
      var dateObj = date.substring(0,10);
      status = restrictDate(dateObj);
    } else if (test4){
      dateObj1 = toDatetime(date.substring(0,10));
      dateObj2 = toDatetime(date.substring(13, 23));
      status = restrictDate(dateObj1);
      status = restrictDate(dateObj2);
      
      var date1_utc = dateObj1.valueOf();
      var date2_utc = dateObj2.valueOf();
      if (date1_utc >= date2_utc){
        status = false;
      }
    } else{
      status = false;
    }
  return status;
}

function highlightErrors() {
  
  var sheet = SpreadsheetApp.getActiveSheet();
  var range = sheet.getRange("L2:L6");
  var dates = range.getValues()
  
  var logRange = sheet.getRange("K1:K1");
  var myLog = logRange.getCell(1,1);
  
  var test = sheet.getRange("M2:M6");
  var test2 = sheet.getRange("N2:N6");
  var test3 = sheet.getRange("O2:O6");
  

  for (i = 1; i <= dates.length; i++){
   
    var testcell = test.getCell(i, 1);
    var testcell2 = test2.getCell(i, 1);
    var testcell3 = test3.getCell(i, 1);
    
    
    var cell = range.getCell(i, 1);
    var background = cell.getBackground();
    
    testcell2.setValue(background);
    
    if (cell.isBlank()) {
      if (background != "#ffffff"){ 
        cell.setBackground("white");
      }
      continue; 
    }
    
    var status = dateCheck(dates[i-1][0]);
    
    testcell3.setValue(status);
    
    if (status == false) {
      cell.setBackground("red");
      
    } else {  
      if (background != "#ffffff"){ 
        cell.setBackground("white");
      }
    }
  }
}

function TEST() {
  var date = new Date("2020-20-20T00:00:00-0000");
  Logger.log(date);
}

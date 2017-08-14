$pdf_mode = 1;
$dvi_mode = 0;
$bibtex = "search_cite.py %R; bibtex %O %B";
$halt_on_error = 1;
$success_cmd = "echo 'WARNINGS' ; echo ; rubber-info --errors %R ; rubber-info --warnings %R; echo";
$failure_cmd = "echo 'ERRORS' ; echo ; rubber-info --errors %R; echo";






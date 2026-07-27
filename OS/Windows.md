
查看 IIS 服务的运行时长, findstr 是查找2024年的

Get-Process | Select-Object w3wp.exe, StartTime, TotalProcessorTime | findstr '2024'

查看服务信息
#### Basic info
tasklist /FI "IMAGENAME eq java.exe" /V

#### More detailed
tasklist /FI "IMAGENAME eq java.exe" /FO LIST /V

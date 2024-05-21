start "client" python client.py 23001
start "local_DNS" python localDNSserver.py 23002
start "root_DNS" python rootDNSserver.py 23003
@REM start "root_DNS" python rootDNSserver2.py 23003
start "com TLD DNS" python comTLDDNSserver.py 23004
@REM start "abcdef company DNS" python companyDNSserver.py 10001 ^<abcdef.txt^>
start "xy company DNS" python companyDNSserver.py 10000 ^<xy.txt^>
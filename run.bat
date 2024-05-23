start "xyz company DNS" python companyDNSserver.py 10002 ^<xyz.txt^>
start "abcdef company DNS" python companyDNSserver.py 10001 ^<abcdef.txt^>
start "xy company DNS" python companyDNSserver.py 10000 ^<xy.txt^>
start "com TLD DNS" python comTLDDNSserver.py 23004
start "root_DNS" python rootDNSserver.py 23003
start "local_DNS" python localDNSserver.py 23002
start "client" python client.py 23001
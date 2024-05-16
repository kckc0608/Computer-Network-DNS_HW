start "client" python client.py 23001
start "local_DNS" python localDNSserver.py 23002
start "root_DNS" python rootDNSserver.py 23003
start "com TLD DNS" python comTLDDNSserver.py 23004
start "company DNS" python companyDNSserver.py 10001
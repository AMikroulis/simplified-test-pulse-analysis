from pkgutil import iter_modules

installed = list(x[1] for x in iter_modules())

required_packages = ['ast', 'datetime','numpy','scipy','matplotlib','os','pyabf','threading','PyQt5','subprocess']

for rqpkg in required_packages:
    if rqpkg in installed:
        pass
    else:
        print ('missing package: '+ str(rqpkg)) 

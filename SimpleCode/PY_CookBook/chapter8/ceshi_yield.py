

def echo(value=None):
    print "Execution starts when 'next()' is called for the first time."
    try:
        while True:
            try:
                value=(yield value)
            except Exception,e:
                value=e
    finally:
        print "Don't forget to clean up when 'close()' is called."



geneator=echo(1)
print geneator.next()
print geneator.next()
print geneator.send(2)

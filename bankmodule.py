
class BankApp:
    '''BankApplication for Customers'''
    ifsc = 100 #Class Variable

    def __init__(self,name, branch, city):
        '''Initilisation of class'''
        BankApp.ifsc += 1
        self.name = name #Object Variable
        self.branch = branch
        self.city = city
        print("Ifsc code is icici00%d "%BankApp.ifsc)

    def info(self):
        print("Bank name is %s, city is %s"%(self.name,self.city))
        print("Brach name is %s "%self.branch)

if __name__ == "__main__":
    B1 = BankApp("ICICI Bank","Anand Nagar","Pune")
    B1.info()
    B2 = BankApp("ICICI Bank","Kothrud","Pune")
    B2.info()
    B3 = BankApp("ICICI Bank","Baner","Pune")
    B3.info()

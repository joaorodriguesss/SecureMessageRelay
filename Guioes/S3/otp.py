import sys
import os

def preproc(str):
      l = []
      for c in str:
          if c.isalpha():
              l.append(c.upper())
      return "".join(l)


def main(inp):
    """ função que executa a funcionalidade pretendida... """
    type = inp[1] 

    if type == 'setup':
        nBytes = inp[2]
        fileW = inp[3]
        iv = os.urandom(nBytes)
        with open(fileW,'w') as file:
            file.write(iv)
    elif type == 'enc':
        fileMessage = inp[2]
        fileKey = inp[3]
        #escrever para o fileMessage.enc
        with open(fileMessage,'r') as fileM, open(fileKey,'w') as fileK:
            
            
    

main(sys.argv)
import sys

# defs auxiliares...
 
def main(inp):
    """ função que executa a funcionalidade pretendida... """
    

    nLines = 0
    nWords = 0
    nChars = 0

    with open(inp[1], "r") as file:

        for line in file:
            if line[-1] == '\n':  nLines +=1
            nWords += len(line.split())
            nChars += len(line)

    print(nLines, nWords, nChars, inp[1])


# Se for chamada como script...
if __name__ == "__main__":
    main(sys.argv)
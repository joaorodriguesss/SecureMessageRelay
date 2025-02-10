import sys


def preproc(str):
      l = []
      for c in str:
          if c.isalpha():
              l.append(c.upper())
      return "".join(l)

def main(inp):
    """ função que executa a funcionalidade pretendida... """
    type = inp[1] 
    shiftList = inp[2]
    #shift = ord(inp[2].upper()) % 65   #65  90
    message = preproc(inp[3])
    result = []
    counter = 0

    if type == 'enc':
        for c in message:
            pos = counter % len(shiftList)
            shift = ord(shiftList[pos].upper()) % 65
            l = ord(c) + shift
            result.append(chr((l -65) % 26 + 65))
            counter += 1
    else:
        for c in message:
            pos = counter % len(shiftList)
            shift = ord(shiftList[pos].upper()) % 65
            l = ord(c) - shift
            result.append(chr((l -65) % 26 + 65))
            counter += 1

    print (''.join(result))

main(sys.argv)
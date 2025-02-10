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
    shift = ord(inp[2].upper()) % 65   #65  90
    message = preproc(inp[3])
    result = []

    if type == 'enc':
        for c in message:
            l = ord(c) + shift
            result.append(chr((l -65) % 26 + 65))
    else:
        for c in message:
            l = ord(c) - shift
            result.append(chr((l -65) % 26 + 65))

    print (''.join(result))

main(sys.argv)
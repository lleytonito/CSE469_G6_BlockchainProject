import struct
import sys

#packFormatHeader is the format recommended by the professor, used as basis for dynamic actual format in packFormatALL
packFormatHeader = '32s d 16s I 12s I'

#These lists are 'synced': each index corresponds to one another, mainly a failsafe for if we need a specific block's format later
formatList = []
blockList = []

#take all inputs (EXCEPT SIZE, WHICH WILL BE DYNAMICALLY CALCULATED) to create a block and append to the blockList
def packFormatAll(prevHash, time, caseID, evidenceID, state, data):
    #get length of data to calculate size
    dataLength = len(data.encode('utf-8'))
    #define new format using size of the data as the last string field's length
    currentBlockFormat = packFormatHeader + ' ' + str(dataLength) + 's'
    #append the new format to formatList
    formatList.append(currentBlockFormat)
    #create a new byte struct of the specified format, and append it to blockList. also return in case it needs immediate use
    newBlock = struct.pack(currentBlockFormat, bytes(prevHash, 'utf-8'), time, bytes(caseID, 'utf-8'), evidenceID, bytes(state, 'utf-8'), dataLength, bytes(data, 'utf-8'))
    blockList.append(newBlock)
    return newBlock

def unpackFromList(index):
    currentBlockFields = []

    #Use index to grab the correct object, then find the last index in it using len
    currentBlock = blockList[index]
    lastIndex = len(currentBlock)

    #this just simplifies later sections, each field is assigned its own bytes variable for conversion
    bytesPrevHash = bytes(currentBlock[0:31])
    bytesTime = bytes(currentBlock[32:40])
    bytesCaseID = bytes(currentBlock[40:55])
    bytesEvidenceID = bytes(currentBlock[56:59])
    bytesState = bytes(currentBlock[60:71])
    bytesSize = bytes(currentBlock[72:75])
    bytesData = bytes(currentBlock[76:lastIndex])


    #convert to human-readable format for each field
    prevHash = (bytesPrevHash.decode('utf-8'))
    time = ((struct.unpack('d', bytesTime))[0])
    caseID = (bytesCaseID.decode('utf-8'))
    evidenceID = (int.from_bytes(bytesEvidenceID, sys.byteorder))
    state = (bytesState.decode('utf-8'))
    size = (int.from_bytes(bytesSize, sys.byteorder))
    data = (bytesData.decode('utf-8'))

    #add all of these fields to a list and then return it (not sure what we should really be doing here so I thought this was a good placeholder)
    currentBlockFields.append(prevHash)
    currentBlockFields.append(time)
    currentBlockFields.append(caseID)
    currentBlockFields.append(evidenceID)
    currentBlockFields.append(state)
    currentBlockFields.append(size)
    currentBlockFields.append(data)

    return currentBlockFields


#example prints, just here for if anyone wants to mess around with testing
print(packFormatAll('abcd', 12.1, '14a', 300, '40a', 'testStringofIndeterminateLength'))
print()
print(unpackFromList(0))

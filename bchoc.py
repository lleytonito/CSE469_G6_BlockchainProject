import binascii
import datetime
import hashlib
import struct
import sys
import argparse
import time
import uuid
import os

#Check datapath to file for init command later
filepath = os.environ.get('BCHOC_FILE_PATH', 'bchoc.bin')

###################################################################################################
#packFormatHeader is the format recommended by the professor, used as basis for dynamic actual format in packFormatALL
packFormatHeader = '32s d 16s I 12s I'

#These lists are 'synced': each index corresponds to one another, mainly a failsafe for if we need a specific block's format later
formatList = []
blockList = []

#take all inputs (EXCEPT SIZE, WHICH WILL BE DYNAMICALLY CALCULATED) to create a block and append to the blockList
#First input is boolean True or False for whether the new object should be written to the file. Should be True in most cases
def packFormatAll(writeToFile, prevHash, time, caseID, evidenceID, state, data):
    #get length of data to calculate size
    dataLength = len(data.encode('utf-8'))
    #define new format using size of the data as the last string field's length
    currentBlockFormat = packFormatHeader + ' ' + str(dataLength) + 's'
    #append the new format to formatList
    formatList.append(currentBlockFormat)

    #hex to bytes
    byteHex = bytes.fromhex(prevHash)

    #data to utf-8 bytes
    byteData = data.encode()

    #create a new byte struct of the specified format, and append it to blockList. also return in case it needs immediate use
    newBlock = struct.pack(currentBlockFormat, byteHex, time, bytes.fromhex(caseID), evidenceID, bytes(state, 'utf-8'), dataLength, byteData)
    blockList.append(newBlock)
    if (writeToFile):
        fileToWrite = open(filepath, 'ab')
        fileToWrite.write(newBlock)
        fileToWrite.close()
    # we weren't using the return here for anything, 
    # so I used the return statement to get the hash version of the block  
    # to make prevHash easier
    hash_object = hashlib.sha256(newBlock)
    hex_dig = hash_object.hexdigest()
    return hex_dig


def unpackFromList(index):
    currentBlockFields = []

    #Use index to grab the correct object, then find the last index in it using len
    currentBlock = blockList[index]
    lastIndex = len(currentBlock)

    #this just simplifies later sections, each field is assigned its own bytes variable for conversion
    bytesPrevHash = bytes(currentBlock[0:32])
    bytesTime = bytes(currentBlock[32:40])
    bytesCaseID = bytes(currentBlock[40:56])
    bytesEvidenceID = bytes(currentBlock[56:60])
    bytesState = bytes(currentBlock[60:72])
    bytesSize = bytes(currentBlock[72:76])
    bytesData = bytes(currentBlock[76:lastIndex])

    #convert to human-readable format for each field
    prevHash = bytesPrevHash.hex()
    time = ((struct.unpack('d', bytesTime))[0])
    caseID = bytesCaseID.hex()
    evidenceID = (int.from_bytes(bytesEvidenceID, sys.byteorder))
    state = (bytesState.decode('utf-8'))
    size = (int.from_bytes(bytesSize, sys.byteorder))
    data = (bytesData.decode())

    #add all of these fields to a list and then return it (not sure what we should really be doing here so I thought this was a good placeholder)
    currentBlockFields.append(prevHash)
    currentBlockFields.append(time)
    currentBlockFields.append(caseID)
    currentBlockFields.append(evidenceID)
    currentBlockFields.append(state)
    currentBlockFields.append(size)
    currentBlockFields.append(data)
    return currentBlockFields

#This function is used to read from the file in init
def unpackFromFile(file, blockOffset, size):
    #Use size argument to find last index for specific block
    lastIndex = (76+size)
    
    #this just simplifies later sections, each field is assigned its own bytes variable for conversion
    bytesPrevHash = bytes(file[blockOffset:blockOffset+32])
    bytesTime = bytes(file[blockOffset+32:blockOffset+40])
    bytesCaseID = bytes(file[blockOffset+40:blockOffset+56])
    bytesEvidenceID = bytes(file[blockOffset+56:blockOffset+60])
    bytesState = bytes(file[blockOffset+60:blockOffset+72])
    bytesSize = bytes(file[blockOffset+72:blockOffset+76])
    bytesData = bytes(file[blockOffset+76:blockOffset+lastIndex])


    #convert to human-readable format for each field
    prevHash = bytesPrevHash.hex()
    time = ((struct.unpack('d', bytesTime))[0])
    caseID = bytesCaseID.hex()
    evidenceID = (int.from_bytes(bytesEvidenceID, sys.byteorder))
    state = (bytesState.decode('utf-8'))
    size = (int.from_bytes(bytesSize, sys.byteorder))+1
    data = (bytesData.decode('utf-8'))
    
    #Pass arguments to packFormatAll with writeToFile = False so the objects are not duplicated in the file
    packFormatAll(False, prevHash, time, caseID, evidenceID, state, data)
        
def generateLists():
    offset = 0
    with open(filepath, 'rb') as file:
        #create a bytearray to read in the file's data
        existingBlocks = bytearray()
        existingBlocks = file.read()
        #check to see if the first block has a size greater than 0 (should be 14 if it is there)
        bytesSize = existingBlocks[72:76]
        size = (int.from_bytes(bytesSize, sys.byteorder))
        #if so, while the size of each block in the file is not 0
        if (size != 0):
            while (size != 0):
                #read the block from the file at the current offset into our arrays that store data structures
                unpackFromFile(existingBlocks, offset, size)
                #increment offset according to base size + size of data string at end of struct
                offset = offset + 76 + size
                #get the new size for the next while loop check
                bytesSize = existingBlocks[offset+72:offset+75]
                size = (int.from_bytes(bytesSize, sys.byteorder))

def writeToFile():
    counter = 0
    with open(filepath, 'wb') as file:
        for item in blockList:
            file.write(item)
    file.close()

def getHash(index):
    hash_object = hashlib.sha256(blockList[index])
    hex_dig = hash_object.hexdigest()
    return hex_dig

def getCurrentHash(index):
    return unpackFromList(index)[0]

def getTime(index):
    return unpackFromList(index)[1]

def getCaseID(index):
    unformattedCaseID = unpackFromList(index)[2]
    formattedCaseID = unformattedCaseID[0:8] + '-' + unformattedCaseID[8:12] + '-' + unformattedCaseID[12:16] + '-' + unformattedCaseID[16:20] + '-' + unformattedCaseID[20:32]
    return formattedCaseID

def getEvidenceID(index):
    return unpackFromList(index)[3]

def getEvidenceIDArray():
    size = len(blockList)
    itemId = []
    for i in range(size):
        itemId.append(getEvidenceID(i))

    return itemId

def getState(index):
    return unpackFromList(index)[4]

def getSize(index):
    return unpackFromList(index)[5]

def getData(index):
    return unpackFromList(index)[6]

def verifyPrevHash(index):
    prevHashStored = getCurrentHash(index)
    if (index == 0):
        prevHashActual = bytes.fromhex('')
        prevHashActual = prevHashActual.hex()
    else:
        prevHashActual = getHash(index-1)
        
    if (prevHashActual == prevHashStored):
        return True
    else:
        return False

def getPrevHash():
    size = len(blockList)
    hash_object = hashlib.sha256(blockList[size-1])
    hex_dig = hash_object.hexdigest()
    return hex_dig
   

def getStatus(itemId):
    itemIdList = getEvidenceIDArray()
    lastIndex = -1
    
    for i in range(len(itemIdList)):
        if itemIdList[i] == itemId:
            lastIndex = i 

    if lastIndex == -1:
        return None

    status = getState(i).strip('\x00')
    return status


###################################################################################################


#add command implementation
def add_command(args):
    #error handling for -c flag (not a valid UUID)
    try:
        uuid.UUID(args.case_id)
    except ValueError:
        print("Invalid UUID for case ID")
        return
    
    if not os.path.isfile(filepath):
        print('Blockchain file not found. Please run init command to initialize the block.')
        return

    generateLists()
    prevHex = getPrevHash()
    itemId = getEvidenceIDArray()
   

    open(filepath, 'ab')
    # Get the current timestamp in seconds
    timestamp = time.time()
    # Convert the timestamp to a datetime object in UTC timezone
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    # Format the datetime object as a string in the desired format
    formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    #  for loop checks for matches between args.item_id and itemId.
    for item in args.item_id:
        # If the item is not in the block, add it to the block and print the required statement
        if item not in itemId:
            formatted_case_id = args.case_id.replace('-', '')
            prevHex = packFormatAll(True, prevHex, time.time(), formatted_case_id, item, 'CHECKEDIN', 'adding')
            print(f'Added Item: {item}')
            print(' Status: CHECKEDIN')
            print(f' Time of Action: {formatted_time}')
        # Else, do not add item to the block
        else :
            print(f'{item} is already in the block and will not be added.')


    generateLists()
    itemId = getEvidenceIDArray()
    print(f'Evidence IDs in the block: {itemId}')
    
#Add a new checkout entry to the chain of custody for the given evidence item. Checkout actions may only be 
#performed on evidence items that have already been added to the blockchain.
def checkout_command(args):
    
    #Check if the file specified by the datapath exists
    if not os.path.isfile(filepath):
        print('Blockchain file not found. Please run init command to initialize the block.')
        return
    
    #Get the list of blocks read from the file as well as the hash of the last block currently in the list
    generateLists()
    prevHex = getPrevHash()

    #Iterate through blockList to verify whether a block with the provided evidence id can be checked out
    i = 0
    canCheckOut = False
    listLength = len(blockList)
    matchingBlockIndex = 0
    
    for i in range(listLength):
        
        #Check if the evidence id at the current block is what was provided as an argument
        if getEvidenceID(i) == args.item_id: 

            #Check if the matching block's status is checked in. If it is not, then it cannot be checked out
            if getState(i)[:9] == "CHECKEDIN":   
                canCheckOut = True
                matchingBlockIndex = i
            else:
                canCheckOut = False

    if canCheckOut:

        #Output the Case ID, Evidence Item ID, Status, and Time of action
        matchingBlock = unpackFromList(matchingBlockIndex)
        print("Case:", matchingBlock[2])                
        print("Checked out item:", matchingBlock[3])  
        print("  Status: CHECKEDOUT")

        # Get the current timestamp in seconds
        timestamp = time.time()
        # Convert the timestamp to a datetime object in UTC timezone
        dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        # Format the datetime object as a string in the desired format
        formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        print("  Time of action:", formatted_time)
        
        #Adds the checkout entry to the chain of custody
        packFormatAll(True, prevHex, time.time(), matchingBlock[2], matchingBlock[3], 'CHECKEDOUT', matchingBlock[6])
    else:
        print("Error: Cannot check out a checked out item. Must check it in first.")

#checkin command implementation
def checkin_command(args):
    generateLists()
    
    offset = 0
    
    i = 0
    checkin = False
    currentBlockFields = []
    matchingindex = 0

    lsitLength = len(blockList)
    for i in range(listLength):
        currentBlockFields = unpackFromList(i)
        if currentBlockFields[3] == args.item_id:
            matchingBlock = currentBlockFields
            
            if currentBlockFields[4] == "CHECKEDOUT":
                checkin = True
                matchingindex = i
            else:
                checkin = False

    if checkin:
        matchingBlock = unpackFromList(matchingindex)
        print("Case:", matchingBlock[2])                
        print("Checked out item:", matchingBlock[3])  
        print("  Status: CHECKEDIN")

        timestamp = time.time()
        dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        print("  Time of action:", formatted_time)
        
        #Adds the checkout entry to the chain of custody
        packFormatAll(True, prevHex, time.time(), matchingBlock[2], matchingBlock[3], 'CHECKEDIN', matchingBlock[6])
    else:
        print("Item can not be checked in. Must be checked out first.")
    # case:
    # checked in item:
    # status:
    # time of action:

#log command implementation
def log_command(args):

    #added this as it'll probably be needed later
    generateLists()
    global blockList

    #Output is given in reverse order (newest entries first)
    if args.reverse:
        blockList.reverse()

    listSize = len(blockList)    

    currentBlock = unpackFromList(0)
    #Check for if there is there is a provided number of entries outputted
    numEntries = 0
    if args.num_entries:
        
        for i in range(listSize):
            
            #Required amount of outputted blocks has been reached
            if numEntries == args.num_entries:
                return
            else:
                currentBlock = unpackFromList(i)
                #Get formatted time for the current block
                dt = datetime.datetime.fromtimestamp(currentBlock[1], tz=datetime.timezone.utc)
                formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
                #A desired Case ID or Item ID is not specified, print the current block
                if args.case_id is None and args.item_id is None:
                    print("Case:", getCaseID(i))
                    print("Item:", currentBlock[3])
                    print("Action:", currentBlock[4])
                    print("Time:", formatted_time)                   
                    print("")
                    numEntries += 1 #The number of logged blocks has increased
                else:
                    canBeLogged = False

                    #Checking for both Case ID and Item ID
                    if args.case_id and args.item_id:
                        if(getCaseID(i) == args.case_id and currentBlock[3] == args.item_id):
                            canBeLogged = True
                    #Check for only looking for Case ID
                    elif args.case_id and args.item_id is None:
                        if(getCaseID(i) == args.case_id):
                            canBeLogged = True
                    #Check for only looking for Item ID
                    elif args.case_id is None and args.item_id:
                        if(currentBlock[3] == args.item_id):
                            canBeLogged = True
                    
                    if canBeLogged == True:
                        print("Case:", getCaseID(i))
                        print("Item:", currentBlock[3])
                        print("Action:", currentBlock[4])
                        print("Time:", formatted_time)
                        print("")
                        numEntries += 1 #The number of logged blocks has increased
                    
    #Print all blocks that match specification (no limit on number of blocks printed)
    else:
        for i in range(listSize):
            
            currentBlock = unpackFromList(i)
            #Get formatted time for the current block
            dt = datetime.datetime.fromtimestamp(currentBlock[1], tz=datetime.timezone.utc)
            formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            #A desired Case ID or Item ID is not specified, print the current block
            if args.case_id is None and args.item_id is None:
                print("Case:", getCaseID(i))
                print("Item:", currentBlock[3])
                print("Action:", currentBlock[4])
                print("Time:", formatted_time)    
                print("")
                numEntries += 1 #The number of logged blocks has increased
            else:
                canBeLogged = False

                #Checking for both Case ID and Item ID
                if args.case_id and args.item_id:
                    if(getCaseID(i) == args.case_id and currentBlock[3] == args.item_id):
                        canBeLogged = True
                #Check for only looking for Case ID
                elif args.case_id and args.item_id is None:
                    if(getCaseID(i) == args.case_id):
                        canBeLogged = True
                #Check for only looking for Item ID
                elif args.case_id is None and args.item_id:
                    if(currentBlock[3] == args.item_id):
                        canBeLogged = True
                    
                if canBeLogged == True:
                    print("Case:", getCaseID(i))
                    print("Item:", currentBlock[3])
                    print("Action:", currentBlock[4])
                    print("Time:", formatted_time)    
                    print("")

#remove command implementation
def remove_command(args):    
    #error handling for -y flag (RELEASED argument without an owner)
    if args.reason == "RELEASED" and not args.owner:
        print("If the reason for removal is RELEASED, an owner must be provided")
        return
    generateLists()
    itemId = getEvidenceIDArray()
    
    matchingIndex = None
    for i,element in enumerate(itemId):
        if element == args.item_id:
            matchingIndex = i
            break

    if matchingIndex is None:
        print("Item ID Not Found. Please try an existing Item ID")
        return
    
    status = getStatus(args.item_id) 

    if status != "CHECKEDIN":
        print(f"Item status is currently {status} and must be CHECKEDIN in order to be removed. Run checkin -i {args.item_id} and try again.")
        return
    
    caseId = getCaseID(matchingIndex)
    formatted_case_id = caseId.replace('-', '')
    prevHash = getPrevHash()
    # Get the current timestamp in seconds
    timestamp = time.time()
    # Convert the timestamp to a datetime object in UTC timezone
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    # Format the datetime object as a string in the desired format
    formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


    packFormatAll(True, prevHash, timestamp, formatted_case_id, args.item_id, args.reason, 'removing')
    print(f"Case: {caseId}")
    print(f"Removed Item: {args.item_id}")
    print(f" Status: {args.reason}")
    if args.owner:
        print(f" Owner Info: {args.owner}")
    print(f" Time of Action: {formatted_time}")

 


#init command implementation
def init_command():
    #offset used for reading more than 1 block from file when they exist
    offset = 0
    #check if the file specified by the check at the top of program exists
    if (os.path.isfile(filepath)):
        #if it does, open the file in read-binary mode
        with open(filepath, 'rb') as file:
            #create a bytearray to read in the file's data
            existingBlocks = bytearray()
            existingBlocks = file.read()
            #check to see if the first block has a size greater than 0 (should be 14 if it is there)
            bytesSize = existingBlocks[72:75]
            size = (int.from_bytes(bytesSize, sys.byteorder))
            #if so, while the size of each block in the file is not 0
            if (size != 0):
                while (size != 0):
                    #read the block from the file at the current offset into our arrays that store data structures
                    unpackFromFile(existingBlocks, offset, size)
                    #increment offset according to base size + size of data string at end of struct
                    offset = offset + 76 + size
                    #get the new size for the next while loop check
                    bytesSize = existingBlocks[offset+72:offset+75]
                    size = (int.from_bytes(bytesSize, sys.byteorder))
            #if the file is empty for some reason, add the initial block as specified in instructions
            else:
                initialBlock = packFormatAll(True, '', time.time(), '00000000000000000000000000000000', 0, 'INITIAL', 'Initial Block')
            print('Blockchain file found with INITIAL block.')

    #if the file does not exist, create it and add the initial block as specified in instructions
    else:
        bcFile = open(filepath, 'wb')
        initialBlock = packFormatAll(True, '', time.time(), '', 0, 'INITIAL', 'Initial Block')
        print('Blockchain file not found. Created INITIAL block.')

    writeToFile()

#verify command implementation
def verify_command():
    generateLists()

    global blockList

    verified = False
    errors = []

    listSize = len(blockList)

    currentBlock = unpackFromList(0)

    for i in range(listSize):
        currentBlock = unpackFromList(i)
        prevHash = getPrevHash()
        # ...

    if verified == True:
        print("Transactions in blockchain: " + listSize)
        print("State of blockchain: CLEAN")
    else:
        print("Transactions in blockchain: " + listSize)
        print("State of blockchain: ERROR")

        #...



#initialize parser with argparse
parser = argparse.ArgumentParser()

#setting subparser "command" to find which command is being used as an argument
subparsers = parser.add_subparsers(dest="command")

#add command takes in two required arguments with flags '-c' and 'i', and '-i' can be taken more than once
add_parser = subparsers.add_parser("add")
add_parser.add_argument("-c", "--case_id", required=True, help="Specifies the case identifier that the evidence is associated with. Must be a valid UUID.")
add_parser.add_argument("-i", "--item_id", type=int, action="append", required=True, help="Specifies the evidence item’s identifier. The item ID must be unique within the blockchain. This means you cannot re-add an evidence item once the remove action has been performed on it.")

#checkout command takes in one required argument with flag '-i'.
checkout_parser = subparsers.add_parser("checkout")
checkout_parser.add_argument("-i", "--item_id",type=int, required=True, help="Specifies the evidence item’s identifier. The item ID must be unique within the blockchain. This means you cannot re-add an evidence item once the remove action has been performed on it.")

#checkin command takes in one required argument with flag '-i'.
checkin_parser = subparsers.add_parser("checkin")
checkin_parser.add_argument("-i", "--item_id",type=int, required=True, help="Specifies the evidence item’s identifier. The item ID must be unique within the blockchain. This means you cannot re-add an evidence item once the remove action has been performed on it.")

#log command takes in four optional arguments: '-r', '-n', '-c', and '-i'. 
# To add implementation for the reverse command, use ( if args["reverse"]: )
log_parser = subparsers.add_parser("log")
log_parser.add_argument("-r", "--reverse", action="store_true", help="Reverses the order of the block entries to show the most recent entries first.")
log_parser.add_argument("-n", "--num_entries", type=int, help="Shows number of block entries.")
log_parser.add_argument("-c", "--case_id", help="Only blocks with the given case_id are returned.")
log_parser.add_argument("-i", "--item_id", type=int, help="Only blocks with the given item_id are returned.")

#remove command takes in two required arguments ('-i' and '-y') and one optional argument (-o)
remove_parser = subparsers.add_parser("remove")
remove_parser.add_argument("-i", "--item_id",type=int, required=True, help="Specifies the evidence item’s identifier. The item ID must be unique within the blockchain. This means you cannot re-add an evidence item once the remove action has been performed on it.")
remove_parser.add_argument("-y", "--reason", required=True, choices=["DISPOSED", "DESTROYED", "RELEASED"], help="Reason for the removal of the evidence item. Must be one of: DISPOSED, DESTROYED, or RELEASED. If the reason given is RELEASED, -o must also be given.")
remove_parser.add_argument("-o", "--owner", help="Information about the lawful owner to whom the evidence was released. At this time, text is free-form and does not have any requirements.")

#init command takes no arguments
init_parser = subparsers.add_parser("init")

#verify command takes no arguments
verify_parser = subparsers.add_parser("verify")

args = parser.parse_args()

#run specified command
if args.command == "add":
    add_command(args)
elif args.command == "checkout":
    checkout_command(args)
elif args.command == "checkin":
    checkin_command(args)
elif args.command == "log":
    log_command(args)
elif args.command == "remove":
    remove_command(args)
elif args.command == "init":
    init_command()
elif args.command == "verify":
    verify_command()
else:
    print("Invalid command")
    parser.print_help()

#!/usr/bin/env python3
import datetime
import hashlib
import struct
import subprocess
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
    if (isinstance(data, str)):
        dataLength = len(data.encode('utf-8'))
    else:
        dataLength = len(data)
    #define new format using size of the data as the last string field's length
    currentBlockFormat = packFormatHeader + ' ' + str(dataLength) + 's'
    #append the new format to formatList
    formatList.append(currentBlockFormat)

    #hex to bytes
    byteHex = bytes.fromhex(prevHash)
    
    #data to utf-8 bytes
    if (isinstance(data, str)):
        byteData = data.encode()
    else:
        byteData = data

    if (isinstance(state, str)):
        byteState = state.encode()
    else:
        byteState = state

    byteArrayCaseID = bytearray.fromhex((caseID))
    byteArrayReversedCaseID = reversed(byteArrayCaseID)
    bytesCaseID = bytes(byteArrayReversedCaseID)

    #create a new byte struct of the specified format, and append it to blockList. also return in case it needs immediate use
    newBlock = struct.pack(currentBlockFormat, byteHex, time, bytesCaseID, evidenceID, byteState, dataLength, byteData)
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
            while (offset < len(existingBlocks)):
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
   
def getStatusIndex(itemId):
    currentStatus = -1
    itemIdList = getEvidenceIDArray()
    for i in range(len(itemIdList)):
        if itemIdList[i] == itemId:
            currentStatus = i

    if currentStatus == -1:
        return None

    return currentStatus

def getStatus(itemId):
    currentStatus = -1
    itemIdList = getEvidenceIDArray()
    for i in range(len(itemIdList)):
        if itemIdList[i] == itemId:
            currentStatus = i
    if currentStatus == -1:
        return None
    status = getState(currentStatus).strip('\x00')
 
    return status


###################################################################################################


#add command implementation
def add_command(args):
    #error handling for -c flag (not a valid UUID)
    try:
        uuid.UUID(args.case_id)
    except ValueError:
        message = "Invalid UUID for case ID"
        sys.stderr.write(message)
        sys.exit(1)
    
    if not os.path.isfile(filepath):
        init_command()

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
            prevHex = packFormatAll(True, prevHex, time.time(), formatted_case_id, item, b'CHECKEDIN\x00\x00', '')
            print(f'Added Item: {item}')
            print(' Status: CHECKEDIN')
            print(f' Time of Action: {formatted_time}')
        # Else, do not add item to the block
        else :
            message = f'{item} is already in the block and will not be added.'
            sys.stderr.write(message)
            sys.exit(1)             
    
#Add a new checkout entry to the chain of custody for the given evidence item. Checkout actions may only be 
#performed on evidence items that have already been added to the blockchain.
def checkout_command(args):
    
    #Check if the file specified by the datapath exists
    if not os.path.isfile(filepath):
        message = 'Blockchain file not found. Please run init command to initialize the block.'
        sys.stderr.write(message)
        raise subprocess.CalledProcessError(1, message)
    
    #Get the list of blocks read from the file as well as the hash of the last block currently in the list
    generateLists()

    itemId = getEvidenceIDArray()
    
    matchingIndex = None
    for i,element in enumerate(itemId):
        if element == args.item_id:
            matchingIndex = i
            break

    if matchingIndex is None:
        message = "Item ID Not Found. Please try an existing Item ID"
        sys.stderr.write(message)
        sys.exit(1)

    status = getStatus(args.item_id) 
    currentStatus = getStatusIndex(args.item_id)
    

    if status != "CHECKEDIN":
        message = f"Item status is currently {status} and must be CHECKEDIN in order to be checked out. Run checkin -i {args.item_id} and try again."
        sys.stderr.write(message)
        sys.exit(1)



    #Output the Case ID, Evidence Item ID, Status, and Time of action
    print("Case:", getCaseID(currentStatus))                
    print("Checked out item:", args.item_id)  
    print("  Status: CHECKEDOUT")

    # Get the current timestamp in seconds
    timestamp = time.time()
    # Convert the timestamp to a datetime object in UTC timezone
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    # Format the datetime object as a string in the desired format
    formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    print("  Time of action:", formatted_time)
        
    prevHex = getHash(matchingIndex)
    #Adds the checkout entry to the chain of custody
    formatted_case_id = getCaseID(currentStatus).replace('-', '')
    packFormatAll(True, '', time.time(), formatted_case_id, args.item_id, b'CHECKEDOUT\x00\x00', '')
 

#checkin command implementation
def checkin_command(args):
    generateLists()
    

    itemId = getEvidenceIDArray()
    
    matchingIndex = None
    for i,element in enumerate(itemId):
        if element == args.item_id:
            matchingIndex = i
            break

    if matchingIndex is None:
        message = "Item ID Not Found. Please try an existing Item ID"
        sys.stderr.write("Item ID Not Found. Please try an existing Item ID")
        sys.exit(1)

    status = getStatus(args.item_id) 
    currentStatus = getStatusIndex(args.item_id)

    if status != "CHECKEDOUT":
        message = f"Item status is currently {status} and must be CHECKEDOUT in order to be checked in. Run checkout -i {args.item_id} and try again."
        sys.stderr.write(message)
        sys.exit(1)

    print("Case:", getCaseID(currentStatus))                
    print("Checked out item:", args.item_id)  
    print("  Status: CHECKEDIN")

    timestamp = time.time()
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    print("  Time of action:", formatted_time)
    prevHex = getHash(matchingIndex)
    #Adds the checkout entry to the chain of custody
    formatted_case_id = getCaseID(currentStatus).replace('-', '')
    packFormatAll(True, '', time.time(), formatted_case_id, args.item_id, b'CHECKEDIN\x00\x00', '')

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
                    print("Action:", currentBlock[4].strip('\x00'))
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
                        print("Action:", currentBlock[4].strip('\x00'))
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
                print("Action:", currentBlock[4].strip('\x00'))
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
                    print("Action:", currentBlock[4].strip('\x00'))
                    print("Time:", formatted_time)    
                    print("")

#remove command implementation
def remove_command(args):    
    #error handling for -y flag (RELEASED argument without an owner)
    if args.why == "RELEASED" and not args.owner:
        message = "If the reason for removal is RELEASED, an owner must be provided"
        sys.stderr.write(message)
        sys.exit(1)

    generateLists()
    itemId = getEvidenceIDArray()
    
    matchingIndex = None
    for i,element in enumerate(itemId):
        if element == args.item_id:
            matchingIndex = i
            break

    if matchingIndex is None:
        message = "Item ID Not Found. Please try an existing Item ID"
        sys.stderr.write(message)
        sys.exit(1)
    
    status = getStatus(args.item_id) 

    if status != "CHECKEDIN":
        message = f"Item status is currently {status} and must be CHECKEDIN in order to be removed. Run checkin -i {args.item_id} and try again."
        sys.stderr.write(message)
        sys.exit(1)
    
    caseId = getCaseID(matchingIndex)
    formatted_case_id = caseId.replace('-', '')
    prevHash = getHash(matchingIndex)
    # Get the current timestamp in seconds
    timestamp = time.time()
    # Convert the timestamp to a datetime object in UTC timezone
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    # Format the datetime object as a string in the desired format
    formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


    packFormatAll(True, '', timestamp, formatted_case_id, args.item_id, args.why.encode() + b'\x00\x00', '')
    print(f"Case: {caseId}")
    print(f"Removed Item: {args.item_id}")
    print(f" Status: {args.why}")
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
                message = "Invalid blockchain file found: exiting program."
                sys.stderr.write(message)
                sys.exit(1)
                #packFormatAll(True, '', time.time(), '00000000000000000000000000000000', 0, 'INITIAL', b'Initial block\x00')
            print('Blockchain file found with INITIAL block.')

    #if the file does not exist, create it and add the initial block as specified in instructions
    else:
        open(filepath, 'wb')
        packFormatAll(True, '', time.time(), '', 0, 'INITIAL', b'Initial block\x00')
        print('Blockchain file not found. Created INITIAL block.')

    writeToFile()

#verify command implementation
def verify_command():
    generateLists()

    global blockList

    verified = False
    errors = []
    parents = []

    listSize = len(blockList)

    for i in range(listSize):
        currentHash = getCurrentHash(i)
        currentVerified = False
        if (currentHash != '0'):
            for j in range(listSize):
                if (currentHash == getHash(j)):
                    currentVerified = True
                    parents.append(getHash(j))
            if (currentVerified == False):
                print("Transactions in blockchain: " + str(listSize))
                print("State of blockchain: ERROR") 
                print("Bad block: " + getHash(i))
                print("Parent block: NOT FOUND")

    for i in range(len(parents)):
        for j in range(len(parents)):
            if ((i != j) and (parents[i] == parents[j])):
                print("Transactions in blockchain: " + str(listSize))
                print("State of blockchain: ERROR") 
                print("Bad block: " + getHash(i))
                print("Parent block: "+ parents[i]) 
                print("Two blocks were found with the same parent.")
                break
        # ...

    if verified == True:
        print("Transactions in blockchain: " + str(listSize))
        print("State of blockchain: CLEAN")
    else:
        print("Transactions in blockchain: " + str(listSize))
        print("State of blockchain: ERROR")
        sys.exit(1)

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
remove_parser.add_argument("-y", "--why", required=True, choices=["DISPOSED", "DESTROYED", "RELEASED"], help="Reason for the removal of the evidence item. Must be one of: DISPOSED, DESTROYED, or RELEASED. If the reason given is RELEASED, -o must also be given.")
remove_parser.add_argument("-o", "--owner", nargs='+', help="Information about the lawful owner to whom the evidence was released. At this time, text is free-form and does not have any requirements.")

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

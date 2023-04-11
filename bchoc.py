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
    newBlock = struct.pack(currentBlockFormat, byteHex, time, bytes(caseID, 'utf-8'), evidenceID, bytes(state, 'utf-8'), dataLength, byteData)
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
    bytesPrevHash = bytes(currentBlock[0:31])
    bytesTime = bytes(currentBlock[32:40])
    bytesCaseID = bytes(currentBlock[40:56])
    bytesEvidenceID = bytes(currentBlock[56:59])
    bytesState = bytes(currentBlock[60:71])
    bytesSize = bytes(currentBlock[72:75])
    bytesData = bytes(currentBlock[76:lastIndex])

    #convert to human-readable format for each field
    prevHash = bytesPrevHash.hex()
    time = ((struct.unpack('d', bytesTime))[0])
    caseID = (bytesCaseID.decode('utf-8'))
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
    bytesPrevHash = bytes(file[blockOffset:blockOffset+31])
    bytesTime = bytes(file[blockOffset+32:blockOffset+40])
    bytesCaseID = bytes(file[blockOffset+40:blockOffset+56])
    bytesEvidenceID = bytes(file[blockOffset+56:blockOffset+59])
    bytesState = bytes(file[blockOffset+60:blockOffset+71])
    bytesSize = bytes(file[blockOffset+72:blockOffset+75])
    bytesData = bytes(file[blockOffset+76:blockOffset+lastIndex])


    #convert to human-readable format for each field
    prevHash = bytesPrevHash.hex()
    time = ((struct.unpack('d', bytesTime))[0])
    caseID = (bytesCaseID.decode('utf-8'))
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
    return unpackFromList(index)[2]

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
            prevHex = packFormatAll(True, prevHex, time.time(), args.case_id, item, 'CHECKEDIN', 'adding')
            print(f'Added Item: {item}')
            print(' Status: CHECKEDIN')
            print(f' Time of Action: {formatted_time}')
            print(prevHex)
        # Else, do not add item to the block
        else :
            print(f'{item} is already in the block and will not be added.')


    
    

#Add a new checkout entry to the chain of custody for the given evidence item. Checkout actions may only be 
#performed on evidence items that have already been added to the blockchain.
def checkout_command(args):
    
    #Offset used for reading a block from the file
    offset = 0
    prevHex = ''
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

                    #Read the block of given size from the file at the current offset the block from the file
                    #at the current offset into the blockList array  
                    unpackFromFile(existingBlocks, offset, size)
                    
                    #increment offset according to base size + size of data string at end of struct
                    offset = offset + 75 + size
                    
                    #continue overwriting prevHex in order to get the hex of the most recent
                    #element of the block
                    hash = existingBlocks[offset:offset+75+size]
                    hash_object = hashlib.sha256(hash)
                    prevHex = hash_object.hexdigest()

                    #get the new size for the next while loop check
                    bytesSize = existingBlocks[offset+72:offset+75]
                    size = (int.from_bytes(bytesSize, sys.byteorder))
        
        #Iterate through blockList to verify whether a block can be checked out
        i = 0
        canCheckOut = False
        currentBlockFields = [] #Contains fields for the current block being accessed
    
        for i in range(blockList.size):
            
            #Get information about the current block being accessed and compare the item id with the argument provided
            currentBlockFields = unpackFromList(i)   

            #Check if the current block is matching with the entered evidence id
            if(currentBlockFields[3] == args.item_id):
                matchingBlock = currentBlockFields

                    #Check for the current state of the evidence item. Only checked in evidence items can be checked out. 
                if(matchingBlock[4] == "CHECKEDIN"):
                    canCheckOut = True
                else:
                    canCheckOut = False

        #Check if the evidence item can be checked in or not
        if(canCheckOut):

            #Output the Case ID, Evidence Item ID, Status, and Time of action
            print("Case:", matchingBlock[2])                
            print("\nChecked out item:", matchingBlock[3])  
            print("\n  Status: CHECKEDOUT")
            currentTime = time.time()
            print("\n  Time of action:", currentTime)

            #Adds the checkout entry to the chain of custody
            packFormatAll(True, prevHex, currentTime, matchingBlock[2], matchingBlock[3], 'CHECKEDOUT', matchingBlock[6])

        else:
            print("Error: Cannot check out a checked out item. Must check it in first.")
    else:
        print('Blockchain file not found. Please run init command to initialize the block.')

#checkin command implementation
def checkin_command(args):
    print("Checkin Command\n Item ID:", args.item_id)

#log command implementation
def log_command(args):
    print("FORMAT LIST")
    print (formatList)
    print("BLOCK LIST")
    print (blockList)
    print("Log Command\n Reverse:", args.reverse)
    if args.num_entries:
        print(" Number of Entries:", args.num_entries)
    if args.case_id:
        print(" Case ID:", args.case_id)
    if args.item_id:
        print(" Item ID:", args.item_id)

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
    
    caseId = getCaseID(matchingIndex)
    prevHash = getPrevHash()
    timeStamp = time.time()
    packFormatAll(True, prevHash, timeStamp, caseId, args.item_id, args.reason, 'removing')
    print(f"Case: {caseId}")
    print(f"Removed Item: {args.item_id}")
    print(f" Status: {args.reason}")
    if args.owner:
        print(f"Owner Info: {args.owner}")
    print(f"Time of Action: {timeStamp}")


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
                initialBlock = packFormatAll(True, '', time.time(), '', 0, 'INITIAL', 'Initial Block')
            print('Blockchain file found with INITIAL block.')

    #if the file does not exist, create it and add the initial block as specified in instructions
    else:
        bcFile = open(filepath, 'wb')
        initialBlock = packFormatAll(True, '', time.time(), '', 0, 'INITIAL', 'Initial Block')
        print('Blockchain file not found. Created INITIAL block.')

    writeToFile()

#verify command implementation
def verify_command():
    print("Verify Command")

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
checkout_parser.add_argument("-i", "--item_id", required=True, help="Specifies the evidence item’s identifier. The item ID must be unique within the blockchain. This means you cannot re-add an evidence item once the remove action has been performed on it.")

#checkin command takes in one required argument with flag '-i'.
checkin_parser = subparsers.add_parser("checkin")
checkin_parser.add_argument("-i", "--item_id", required=True, help="Specifies the evidence item’s identifier. The item ID must be unique within the blockchain. This means you cannot re-add an evidence item once the remove action has been performed on it.")

#log command takes in four optional arguments: '-r', '-n', '-c', and '-i'. 
# To add implementation for the reverse command, use ( if args["reverse"]: )
log_parser = subparsers.add_parser("log")
log_parser.add_argument("-r", "--reverse", action="store_true", help="Reverses the order of the block entries to show the most recent entries first.")
log_parser.add_argument("-n", "--num_entries", type=int, help="Shows number of block entries.")
log_parser.add_argument("-c", "--case_id", help="Only blocks with the given case_id are returned.")
log_parser.add_argument("-i", "--item_id", help="Only blocks with the given item_id are returned.")

#remove command takes in two required arguments ('-i' and '-y') and one optional argument (-o)
remove_parser = subparsers.add_parser("remove")
remove_parser.add_argument("-i", "--item_id", required=True, help="Specifies the evidence item’s identifier. The item ID must be unique within the blockchain. This means you cannot re-add an evidence item once the remove action has been performed on it.")
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

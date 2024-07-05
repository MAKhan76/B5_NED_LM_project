# main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
#from fastapi_neon import settings
import fitz  # PyMuPDF
import re
import json
from pydantic import BaseModel
#from sqlmodel import create_engine, SQLModel, Session, Field, select
from typing import Optional, List, Annotated
from contextlib import asynccontextmanager
import tabula

app = FastAPI()


class FileData(BaseModel):
    name: str
    valid: bool
    file_status: str

def extract_text_from_pdf(pdf_path):
    # Your existing PDF extraction code here...
    # Assume the rest of the implementation is the same as provided in the initial script
    pdf_document = fitz.open(pdf_path)
    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text("text")
        test1 = page.get_text("text")
       # print (test1)
        text += "\n\n--- End of Page ---\n\n"
        text += "\n\n--- End of Page {} ---\n\n".format(page_num + 1)  # Optional: add page delimiters
    return text

def separate_string(sample_data):
    separated_values = sample_data.split('/')
    cleaned_values = [value.strip() for value in separated_values]
    return cleaned_values

def check_item_type(item):
    # Check if the item is a number by trying to convert it to float
    try:
        float(item)
        return "nb"
    except ValueError:
        # Use regular expression to check for alphabetic-only strings
        if re.match(r'^[a-zA-Z]+$', item):
            return "Ch"
        else:
            return "st"

def extract_patient_data(text):
    # Your existing patient data extraction code here...
    # Assume the rest of the implementation is the same as provided in the initial script
    lines = text.splitlines()
    patient_data = {}
    report_data = []
    sample_type = []
    explanation = []
    
    pattern = ".+"  # character sequences
    l = re.findall(pattern, text, re.IGNORECASE)
    
    x = 0
    R = ""
    Page1 = 0 
    Page2 = 0
    Page3 = 0
    page4 = 0
    page5 = 0
    Page6 = 0

    explanation_start = 0
    Summary_start = 0
    Explanation_report ="F"
    for i in range(len(l)):
        if l[i] == "07736918467" and x < 1:
            x = i
        if l[i] == "Report Explanation" and Explanation_report != "T":
            R = "T"
            explanation_start = i
            if i < 12:
                Explanation_report="T"
            else:
                Explanation_report="F"
        else:
            R = "F"
        if l[i] == "Summary" and Summary_start == 0:
            Summary_start = i

       # print(R)
        #print(explanation_start)
       
    if x: 
        patient_data["surname"] = l[x + 1]
        patient_data["forename"] = l[x + 2]
        patient_data["dateOfBirth"] = l[x + 3]
        patient_data["sampleNumber"] = l[x + 4]
        patient_data["sex"] = l[x + 5]
        patient_data["labNo"] = l[x + 6]
        patient_data["sampleDated"] = l[x + 7]
        patient_data["sampleReceived"] = l[x + 8]
        patient_data["resultReported"] = l[x + 9]
        sample_type_raw =l[x+ 10]
        sample_type = separate_string(sample_type_raw)
        patient_data["sampleType"] = sample_type

        #sample_type.append(l[x + 10])
        #patient_data["sampleType"] = sample_type
        
        # Assuming tests start right after the sample type and continue until "Report Explanation"
        test_start = x + 12
        test_end = Page1
      #  print(R)
       # print(Explanation_report)
       # print(Summary_start)
    if R == "F" and Explanation_report=="F" and Summary_start==0:
        explanation_start = 0  
      #  print("Test")  
        TSPage_Start=[]
        TSPage_End=[]
        for f in range(0, len(l)):
            
            if l[f] == "07736918467":
                TSPage_Start.append(f+11)
            elif l[f] == '--- End of Page ---':
                TSPage_End.append(f-1)
               
       # print(TSPage_Start)
       # print(TSPage_End)
        testresults=[]
        testname=""
        for j in range(0,len(TSPage_End)-1):
            print(l[TSPage_Start[j]:TSPage_End[j]])
            TResults=l[TSPage_Start[j]:TSPage_End[j]]
            for g in range(0,len(TResults)-1):
                RType1 = check_item_type(TResults[g])
                RType2 = check_item_type(TResults[g+1])
                if RType1=="Ch" and RType2=="Ch" and len(TResults[g+1])>2:
                    TestType=TResults[g]+" " +TResults[g+1]
                    test = {
                            "test":TestType,
                            "patientResult":TResults[g+2],
                            "normalRange": TResults[g+4],
                            "units": TResults[g+3]
                        }
                    report_data.append(test)
                elif RType1=="Ch" and RType2=="nb":
                     TestType=TResults[g]
                     test = {
                            "test":TestType,
                            "patientResult":TResults[g+1],
                            "normalRange": TResults[g+3],
                            "units": TResults[g+2]
                        }
                     report_data.append(test)
                elif RType1=="Ch" and RType2=="Ch" and len(TResults[g+1])<2:
                    TestType=TResults[g]+" "+TResults[g+1]
                    test = {
                            "test":TestType,
                            "patientResult":TResults[g+2],
                            "normalRange": TResults[g+4],
                            "units": TResults[g+3]
                        }
                    report_data.append(test)
       # print(testresults)
        
        for i   in range(0, 1):#len(TSPage_Start)):
            for h in range(TSPage_Start[i],TSPage_End[i]):
               # print(l[h])
                result = check_item_type(l[h])
              #  print(f"The item '{l[h]}' is a {result}.")
    
                if (result=="ch" or result=="st") and len(l[h])>3:
                  #  print(f"test value 1 '{h}'")
                    if result=="ch" and len(l[h])>3:
                      #  print("test value string")
                        testname=len(l[h-1]) # +"\n"  + len(l[h])
                        test = {
                            "test":l[h-1:h],
                            "patientResult": l[h+1],
                            "normalRange": l[h+3],
                            "units": l[h+2]
                        }
                    else:
                        testname=len(l[h])
                        test = {
                            "test":l[h],
                            "patientResult": l[h+1],
                            "normalRange": l[h+3],
                            "units": l[h+2]
                        }

                   # print(f"test value '{testname}'")
                   # print(f"test value fff '{l[h]}'")
                                                                                                                                    
                h = h+4
             
       # print(TSPage_Start)
       # print(TSPage_End)
        for i in range(test_start, test_end, 4):
            TY=""
            y=0
            if l[i+2] == "H" or l[i+2] == "L":
                TY=l[i+2]
                y=1
            
            if i + 3 < test_end:
                test = {
                    "test": l[i] + " "+ TY,
                    "patientResult": l[i + 1],
                    "normalRange": l[i + 3+y],
                    "units": l[i + 2+y]
                 }
              #  report_data.append(test)
    #print("explanation_start")
    #print(explanation_start)
    #print(R)
    if R == "T" or (explanation_start>0 and explanation_start<67) :           
      #  print("Explanation test")
       # print(Summary_start)
        Summary_end = len(l)
       # print(Summary_end)
        Result=[]
        Rrenge=[]
        Pages=[]
        End_Explanation = 0
        for i in range(Summary_start, Summary_end):
          # print(l[i])
           if l[i]=='Result':
             #  print("Result")
               Result.append(i)
           elif l[i]=='Range':
                Rrenge.append(i)
           elif l[i]=='--- End of Page ---':
                Pages.append(i)
       # print(Result)
       # print(Rrenge)
       # print(Pages)
        ExSummary = "\n".join(l[Summary_start :Result[0]-1])
       # ExSummary ={"Summary":l[Summary_start :Result[0]-1]}
        explanation.append(ExSummary)
        p=0
        for i in range(0, len(Result)-1):
           # print(Result[i])
            #print(len(Result))
            #print(i)
            #print("resultsvalue")
            #print(len(Pages))
            #sprint(p)

            if Result[i+1]>Pages[p]:
               # print("end exp")
                End_Explanation = Pages[p]-1
                p=p+1
            else:
                End_Explanation = Result[i+1]-1
            #if i + 3 < len(Result)-1:
            test = {
                "test": l[Result[i]-1],
                "Result": "\n".join(l[Result[i]+1 :Rrenge[i]]),
                "Range": l[Rrenge[i]+1],
                "units": l[Rrenge[i]+2],
                "Explanation": "\n".join(l[Rrenge[i]+3 :End_Explanation]) 
                }
          #  report_data.append(test)
            explanation.append(test)
           
            if p==len(Pages)-1:
                    test = {
                        "test": l[Result[-1]-1],
                        "Result": "\n".join(l[Result[-1]+1 :Rrenge[-1]]),
                        "Range": l[Rrenge[-1]+1],
                        "units": l[Rrenge[-1]+2],
                        "Explanation": "\n".join(l[Rrenge[-1]+3 :Pages[p]-1]) 
                        }
                    explanation.append(test)
    return {
        "patientData": patient_data,
        "reportData": report_data,
        "explanation": explanation
    }
@app.post("/extract/")
async def extract_data(file: UploadFile = File(...)):
    try:
        # Process your file here
        # For example, save it temporarily, process, and delete if needed
                #text = extract_text_from_pdf(file.filename)
               #print(text)
                #if text:
                    # Process the extracted text to get patient data
                  #  data = extract_patient_data(text)
                    return {"filename": file.filename}
                  #  return {"data": data}
                #else:
                 #   raise HTTPException(status_code=404, detail="No text found in the PDF.")
                
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
    except Exceptio3n as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
            
            

@app.get("/extract/{pdf_path}", response_model=dict)
async def extract_pdf_data(pdf_path: str):
    try:
        # Ensure the file is a PDF
        if not pdf_path.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        print(pdf_path)
        # Extract text from the PDF
        text = extract_text_from_pdf(pdf_path)
        if text:
            # Process the extracted text to get patient data
            data = extract_patient_data(text)
            return {"data": data}
        else:
            raise HTTPException(status_code=404, detail="No text found in the PDF.")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# You can include additional API endpoints as needed

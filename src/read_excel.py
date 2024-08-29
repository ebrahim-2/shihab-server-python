import os
import pandas as pd
from neo4j import GraphDatabase
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

router = APIRouter()

class ExcelProcessor:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    async def process_excel(self, file: UploadFile):
        try:
            df = pd.read_excel(file.file)
            data = df.to_dict('records')

            for row in data:
                if 'Invoice Code' in row:
                    await self.process_sales(row)
                elif 'Return Code' in row:
                    await self.process_returns(row)

            return {"message": "Excel file processed successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def process_sales(self, row):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Customer {code: $customerCode})
                ON CREATE SET c.name = $customerName, c.phone = toInteger($phoneNumber), c.address = $address
                MERGE (s:Salesman {code: toInteger($salesmanCode)})
                ON CREATE SET s.name = $salesmanName
                MERGE (i:Product {code: toInteger($itemCode)})
                ON CREATE SET i.name = $itemName, i.priceBig = toInteger($priceBig), i.priceMedium = toInteger($priceMedium), i.priceSmall = toInteger($priceSmall), i.bigUnit = $bigUnit, i.mediumUnit = $mediumUnit, i.smallUnit = $smallUnit
                MERGE (a:Area {name: $area})
                MERGE (o:Order {invoiceCode: $invoiceCode})
                ON CREATE SET o.invoiceDate = datetime($date), o.discountAmount = toInteger($discountAmount), o.lineAmount = toInteger($lineAmount)
                MERGE (c)-[:PLACED_ORDER]->(o)
                MERGE (s)-[:SOLD_ORDER]->(o)
                MERGE (o)-[saleP:CONTAINS_PRODUCT]->(i)
                MERGE (o)-[:DELIVERED_IN]->(a)
                MERGE (c)-[:LOCATED_IN]->(a)
                SET saleP.batchNumber = $batchNumber,
                saleP.bigQuantity = toInteger($bigQuantity),
                saleP.mediumQuantity = toInteger($mediumQuantity),
                saleP.smallQuantity = toInteger($smallQuantity)
                """,
                self.prepare_sales_params(row)
            )

    async def process_returns(self, row):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Customer {code: $customerCode})
                ON CREATE SET c.name = $customerName, c.phone = toInteger($phoneNumber), c.address = $address
                MERGE (s:Salesman {code: toInteger($salesmanCode)})
                ON CREATE SET s.name = $salesmanName
                MERGE (i:Product {code: toInteger($itemCode)})
                ON CREATE SET i.name = $itemName, i.priceBig = toInteger($priceBig), i.priceMedium = toInteger($priceMedium), i.priceSmall = toInteger($priceSmall), i.bigUnit = $bigUnit, i.mediumUnit = $mediumUnit, i.smallUnit = $smallUnit
                MERGE (a:Area {name: $area})
                MERGE (o:Order {invoiceCode: $invoiceCode})
                MERGE (r:Return {returnCode: $returnCode})
                ON CREATE SET r.returnDate = datetime($date),  r.returnedAmount = toInteger($lineAmount)
                MERGE (c)-[:RETURNED]->(r)
                MERGE (r)-[:RETURNED_TO]->(s)
                MERGE (r)-[returnedP:RETURNED_PRODUCT]->(i)
                MERGE (r)-[:RETURNED_IN]->(a)
                MERGE (r)-[:RETURNED_FROM]->(o)
                SET returnedP.batchNumber = $batchNumber,
                returnedP.bigQuantity = toInteger($bigQuantity),
                returnedP.mediumQuantity = toInteger($mediumQuantity),
                returnedP.smallQuantity = toInteger($smallQuantity)
                """,
                self.prepare_returns_params(row)
            )

    def prepare_sales_params(self, row):
        return {
            'customerCode': row['Customer Code'],
            'customerName': row['Customer Name'],
            'phoneNumber': row['Phone number'],
            'address': row['Address'],
            'area': row['Area'],
            'salesmanCode': row['Salesman Code'],
            'salesmanName': row['Salesman Name'],
            'itemCode': row['Item Code'],
            'itemName': row['Item Name'],
            'invoiceCode': row['Invoice Code'],
            'date': pd.to_datetime(f"{row['Invoice Date']} {row['Invoice Time']}").isoformat(),
            'batchNumber': row['Batch Number'],
            'discountAmount': row['Discount Amount'],
            'totalAmount': row['Line Amount'],
            'bigQuantity': self.parse_float_or_null(row['Big Quantity']),
            'bigUnit': self.parse_string_or_null(row['Big Unit']),
            'priceBig': self.parse_float_or_null(row['Price Big']),
            'mediumQuantity': self.parse_int_or_null(row['Medium Quantity']),
            'mediumUnit': self.parse_string_or_null(row['Medium Unit']),
            'priceMedium': self.parse_float_or_null(row['Price Medium']),
            'smallQuantity': self.parse_int_or_null(row['Small Quantity']),
            'smallUnit': self.parse_string_or_null(row['Small Unit']),
            'priceSmall': self.parse_float_or_null(row['Price Small']),
            'lineAmount': row['Line Amount'],
        }

    def prepare_returns_params(self, row):
        return {
            'customerCode': row['Customer Code'],
            'customerName': row['Customer Name'],
            'phoneNumber': row['Phone number'],
            'address': row['Address'],
            'area': row['Area'],
            'salesmanCode': row['Salesman Code'],
            'salesmanName': row['Salesman Name'],
            'itemCode': row['Item Code'],
            'itemName': row['Item Name'],
            'invoiceCode': row['Invoice Code'],
            'date': pd.to_datetime(f"{row['Return Date']} {row['Return Time']}").isoformat(),
            'batchNumber': row['Batch Number'],
            'totalAmount': row['Line Amount'],
            'bigQuantity': self.parse_float_or_null(row['Big Quantity']),
            'bigUnit': self.parse_string_or_null(row['Big Unit']),
            'priceBig': self.parse_float_or_null(row['Price Big']),
            'mediumQuantity': self.parse_int_or_null(row['Medium Quantity']),
            'mediumUnit': self.parse_string_or_null(row['Medium Unit']),
            'priceMedium': self.parse_float_or_null(row['Price Medium']),
            'smallQuantity': self.parse_int_or_null(row['Small Quantity']),
            'smallUnit': self.parse_string_or_null(row['Small Unit']),
            'priceSmall': self.parse_float_or_null(row['Price Small']),
            'lineAmount': row['Line Amount'],
            'returnCode': row['Return Code'],
        }

    @staticmethod
    def parse_float_or_null(value):
        return float(value) if pd.notna(value) else None

    @staticmethod
    def parse_int_or_null(value):
        return int(value) if pd.notna(value) else None

    @staticmethod
    def parse_string_or_null(value):
        return str(value) if pd.notna(value) else None

excel_processor = ExcelProcessor()

@router.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    return await excel_processor.process_excel(file)
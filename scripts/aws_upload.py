# scripts/aws_upload.py
import boto3
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError

load_dotenv()


def upload_to_s3():
    """Sube inventario_diario.csv a S3"""
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        print("🚀 Subiendo inventario_diario.csv...")
        s3.upload_file(
            "inventario.csv", os.getenv("AWS_BUCKET_NAME"), "inventario_diario.csv"
        )
        print("✅ Archivo subido exitosamente")

    except ClientError as e:
        print(f"❌ Error AWS: {e}")
    except FileNotFoundError:
        print("❌ Archivo inventario.csv no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    upload_to_s3()

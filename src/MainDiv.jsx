import React, { useState } from "react";
import { v4 as uuidv4 } from "uuid";

export default function MainDiv() {
  const [reference, setReference] = useState(null);
  const [products, setProducts] = useState([]);
  const [batchId] = useState(uuidv4()); // fixed per session/batch ✅
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false); // waiting for Lambda
  const [downloadReady, setDownloadReady] = useState(false);

  const handleReferenceChange = (e) => {
    const file = e.target.files[0];
    if (file) setReference(file);
  };

  const handleProductsChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length) setProducts(files);
  };

  const uploadAll = async () => {
    if (!reference && products.length === 0) {
      alert("Please select at least one file first.");
      return;
    }

    setUploading(true);
    try {
      // Upload reference first
      if (reference) {
        const refFilename = `${batchId}-reference-${reference.name}`;
        await uploadFile(reference, refFilename);
      }

      // Upload all products
      const productUploads = products.map((file, i) => {
        const filename = `${batchId}-product-${i + 1}-${file.name}`;
        return uploadFile(file, filename);
      });
      await Promise.all(productUploads);

      alert("✅ All files uploaded successfully!");

      // Start waiting for Lambda to process
      setProcessing(true);
      setTimeout(() => {
        setProcessing(false);
        setDownloadReady(true);
      }, 10000); // wait 10s for Lambda to finish
    } catch (err) {
      console.error("Batch upload failed:", err);
      alert("❌ Error uploading files");
    } finally {
      setUploading(false);
    }
  };

  const uploadFile = async (file, filename) => {
    const res = await fetch(
      `https://7j2iuj1858.execute-api.eu-central-1.amazonaws.com/Prod/spio-images-uploads/${encodeURIComponent(
        filename
      )}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": file.type || "application/octet-stream",
        },
        body: file,
      }
    );

    if (res.status < 200 || res.status >= 300) {
      console.error(`Upload failed: ${filename} (${res.status})`);
      throw new Error(`Upload failed: ${filename}`);
    }

    console.log("✅ Uploaded:", filename);
  };

  const downloadZip = () => {
    let downloadId = batchId.split("-")[0];
    const url = `https://spio-images-processing.s3.eu-central-1.amazonaws.com/${downloadId}/scaled/${downloadId}_scaled.zip`;
    const link = document.createElement("a");
    link.href = url;
    link.download = `${batchId}_scaled.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Reset the form after download
    setReference(null);
    setProducts([]);
    setDownloadReady(false);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        backgroundColor: "#f3f4f6",
        padding: "1rem",
      }}
    >
      <h1>Serverless Product Image Optimizer</h1>
      <div
        style={{
          backgroundColor: "#fff",
          borderRadius: "1rem",
          padding: "2rem",
          maxWidth: "400px",
          width: "100%",
          textAlign: "center",
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
        }}
      >
        <h1
          style={{
            fontSize: "1.5rem",
            fontWeight: "bold",
            marginBottom: "1.5rem",
            color: "#1f2937",
          }}
        >
          Image Upload
        </h1>

        {/* Reference Upload */}
        <label
          style={{
            display: "block",
            marginBottom: "1.5rem",
            cursor: "pointer",
          }}
        >
          <span
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontWeight: 500,
              color: "#374151",
            }}
          >
            Reference
          </span>
          <input
            type="file"
            accept="image/*"
            onChange={handleReferenceChange}
            style={{ display: "none" }}
          />
          <div
            style={{
              border: "2px dashed #d1d5db",
              borderRadius: "0.75rem",
              padding: "1.5rem",
            }}
          >
            {reference ? (
              <p style={{ color: "#059669", fontWeight: 500 }}>
                {reference.name}
              </p>
            ) : (
              <p style={{ color: "#6b7280" }}>
                Click to select a reference image
              </p>
            )}
          </div>
        </label>

        {/* Product Images Upload */}
        <label
          style={{
            display: "block",
            marginBottom: "1.5rem",
            cursor: "pointer",
          }}
        >
          <span
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontWeight: 500,
              color: "#374151",
            }}
          >
            Product Images
          </span>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handleProductsChange}
            style={{ display: "none" }}
          />
          <div
            style={{
              border: "2px dashed #d1d5db",
              borderRadius: "0.75rem",
              padding: "1.5rem",
            }}
          >
            {products.length > 0 ? (
              <p style={{ color: "#059669", fontWeight: 500 }}>
                {products.length} file(s) selected
              </p>
            ) : (
              <p style={{ color: "#6b7280" }}>Click to select product images</p>
            )}
          </div>
        </label>

        {/* Upload All Button */}
        <button
          onClick={uploadAll}
          disabled={uploading || processing}
          style={{
            backgroundColor: uploading || processing ? "#9ca3af" : "#2563eb",
            color: "#fff",
            fontWeight: "bold",
            padding: "0.75rem 1.5rem",
            borderRadius: "0.5rem",
            cursor: uploading || processing ? "not-allowed" : "pointer",
            width: "100%",
            transition: "background 0.2s",
            marginBottom: "1rem",
          }}
        >
          {uploading
            ? "Uploading..."
            : processing
            ? "Processing..."
            : "Upload All"}
        </button>

        {/* Download Zip Button */}
        {downloadReady && (
          <button
            onClick={downloadZip}
            style={{
              backgroundColor: "#16a34a",
              color: "#fff",
              fontWeight: "bold",
              padding: "0.75rem 1.5rem",
              borderRadius: "0.5rem",
              cursor: "pointer",
              width: "100%",
              transition: "background 0.2s",
            }}
          >
            Download Scaled Batch
          </button>
        )}
      </div>
    </div>
  );
}

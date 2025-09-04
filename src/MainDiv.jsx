import React, { useState } from "react";

export default function MainDiv() {
  const [reference, setReference] = useState(null);
  const [products, setProducts] = useState([]);

  const handleReferenceChange = (e) => {
    const file = e.target.files[0];
    if (file) setReference(file);
  };

  const handleProductsChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length) setProducts(files);
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
              transition: "0.2s border",
            }}
          >
            {reference ? (
              <p style={{ color: "#059669", fontWeight: 500 }}>
                {reference.name}
              </p>
            ) : (
              <p style={{ color: "#6b7280" }}>
                Click to upload a reference image
              </p>
            )}
          </div>
        </label>

        {/* Product Images Upload */}
        <label
          style={{ display: "block", marginBottom: "1rem", cursor: "pointer" }}
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
              transition: "0.2s border",
            }}
          >
            {products.length > 0 ? (
              <p style={{ color: "#059669", fontWeight: 500 }}>
                {products.length} file(s) selected
              </p>
            ) : (
              <p style={{ color: "#6b7280" }}>Click to upload product images</p>
            )}
          </div>
        </label>
      </div>
    </div>
  );
}

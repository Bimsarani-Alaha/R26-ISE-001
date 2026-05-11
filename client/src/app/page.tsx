"use client";

import { useState } from "react"; // React state management

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [resultImage, setResultImage] = useState<string>("");
  const [measurements, setMeasurements] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => { //Runs when user selects an image
    const f = e.target.files?.[0];
    if (!f) return;

    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResultImage("");  //Reset Previous Results
    setMeasurements([]);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select an image before predicting.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setMessage("");

    try {
      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`); //check API response
      }

      const data = await res.json();

      setResultImage(data.annotated_image); //Set Annotated Image
      setMeasurements(data.measurements || []);
      if (!data.measurements || data.measurements.length === 0) {
        setMessage("Prediction completed but no measurement data was returned.");
      }
    } catch (err) { //error handling for network issues or server errors
      console.error(err);
      setMessage("Error connecting to server. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell">
      <section className="card">
        <div className="hero">
          <div>
            <h1>Pose Detection Demo</h1>
            <p>Upload an image to predict pose measurements and view the annotated result.</p>
          </div>
          <div className="actions">
            <label className="file-input-label">
              <span>Select Image</span>
              <input type="file" accept="image/*" onChange={handleChange} />
            </label>
            {file && <div className="file-name">{file.name}</div>}
            <button className="predict-button" onClick={handleUpload} disabled={loading}> 
              {loading ? "Processing..." : "Predict Image"}
            </button>
          </div>
        </div>

        {message && <div className="info-box">{message}</div>}
      </section>

      <section className="results">
        {(preview || resultImage) && (
          <div className="image-grid">
            {preview && (
              <div className="image-card">
                <h3>Original</h3>
                <img src={preview} alt="Original upload preview" />
              </div>
            )}
            {resultImage && (
              <div className="image-card">
                <h3>Result</h3>
                <img src={resultImage} alt="Annotated result" />
              </div>
            )}
          </div>
        )}

        {measurements.length > 0 && (
          <div className="measurements-card">
            <h3>Measurements</h3>
            {measurements.map((m, i) => (
              <div className="measurement-row" key={i}>
                <div>
                  <strong>Shoulder:</strong> {m.shoulder_width?.toFixed(1) ?? "N/A"}
                </div>
                <div>
                  <strong>Hip:</strong> {m.hip_width?.toFixed(1) ?? "N/A"}
                </div>
                <div>
                  <strong>Height:</strong> {m.height?.toFixed(1) ?? "N/A"}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

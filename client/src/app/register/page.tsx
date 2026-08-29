"use client";

import { ArrowRight } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { saveSystemData } from "@/app/lib/systemSaveApi";

type FormValues = {
  name: string;
  phone: string;
  email: string;
  age: string;
  password: string;
  confirmPassword: string;
};

const initialValues: FormValues = {
  name: "",
  phone: "",
  email: "",
  age: "",
  password: "",
  confirmPassword: "",
};

export default function RegisterPage() {
  const router = useRouter();
  const [values, setValues] = useState(initialValues);
  const [error, setError] = useState("");

  const updateField = (field: keyof FormValues, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));
    setError("");
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (Number(values.age) < 13 || Number(values.age) > 120) {
      setError("Please enter an age between 13 and 120.");
      return;
    }

    if (values.password.length < 8) {
      setError("Your password must be at least 8 characters.");
      return;
    }

    if (values.password !== values.confirmPassword) {
      setError("Your passwords do not match.");
      return;
    }

    try {
      await saveSystemData({
        name: values.name,
        phone: values.phone,
        email: values.email,
        age: Number(values.age),
        password: values.password,
      });
      router.push("/input");
    } catch (saveError) {
      const message =
        saveError instanceof Error
          ? saveError.message
          : "Unable to save your account at the moment.";
      setError(message);
    }
  };

  const fieldClassName =
    "w-full border border-[#ddd] bg-white px-4 py-3 text-sm text-[#111] outline-none transition-colors placeholder:text-[#c2c2c2] focus:border-[#111]";

  return (
    <div className="min-h-screen w-full bg-white text-[#111]">
      <SiteNav centered />

      <main className="mx-auto w-full max-w-2xl px-6 py-14 md:py-20">
        <motion.header
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-10 text-center"
        >
          <p
            className="mb-4 text-[10px] tracking-[0.3em] text-[#aaa]"
            style={SANS}
          >
            YOUR STYLE JOURNEY STARTS HERE
          </p>
          <h1
            className="mb-4 text-4xl tracking-wide md:text-5xl"
            style={{ ...SERIF, fontWeight: 300 }}
          >
            Create your account
          </h1>
          <p
            className="text-sm tracking-wide text-[#888]"
            style={{ ...SANS, fontWeight: 300 }}
          >
            Save your preferences and make every recommendation feel like yours.
          </p>
        </motion.header>

        <motion.form
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.12 }}
          onSubmit={handleSubmit}
          className="border-t border-[#e8e8e8] pt-8"
        >
          <div className="grid gap-6 md:grid-cols-2">
            <div className="md:col-span-2">
              <label
                htmlFor="name"
                className="mb-2 block text-[10px] tracking-[0.25em] text-[#999]"
                style={SANS}
              >
                FULL NAME
              </label>
              <input
                id="name"
                name="name"
                type="text"
                required
                autoComplete="name"
                value={values.name}
                onChange={(event) => updateField("name", event.target.value)}
                placeholder="Your name"
                className={fieldClassName}
              />
            </div>

            <div>
              <label
                htmlFor="phone"
                className="mb-2 block text-[10px] tracking-[0.25em] text-[#999]"
                style={SANS}
              >
                PHONE NUMBER
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                required
                autoComplete="tel"
                value={values.phone}
                onChange={(event) => updateField("phone", event.target.value)}
                placeholder="+94 77 123 4567"
                className={fieldClassName}
              />
            </div>

            <div>
              <label
                htmlFor="age"
                className="mb-2 block text-[10px] tracking-[0.25em] text-[#999]"
                style={SANS}
              >
                AGE
              </label>
              <input
                id="age"
                name="age"
                type="number"
                required
                min="13"
                max="120"
                value={values.age}
                onChange={(event) => updateField("age", event.target.value)}
                placeholder="Your age"
                className={fieldClassName}
              />
            </div>

            <div className="md:col-span-2">
              <label
                htmlFor="email"
                className="mb-2 block text-[10px] tracking-[0.25em] text-[#999]"
                style={SANS}
              >
                EMAIL ADDRESS
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                autoComplete="email"
                value={values.email}
                onChange={(event) => updateField("email", event.target.value)}
                placeholder="you@example.com"
                className={fieldClassName}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-[10px] tracking-[0.25em] text-[#999]"
                style={SANS}
              >
                PASSWORD
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={values.password}
                onChange={(event) =>
                  updateField("password", event.target.value)
                }
                placeholder="At least 8 characters"
                className={fieldClassName}
              />
            </div>

            <div>
              <label
                htmlFor="confirm-password"
                className="mb-2 block text-[10px] tracking-[0.25em] text-[#999]"
                style={SANS}
              >
                CONFIRM PASSWORD
              </label>
              <input
                id="confirm-password"
                name="confirmPassword"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={values.confirmPassword}
                onChange={(event) =>
                  updateField("confirmPassword", event.target.value)
                }
                placeholder="Repeat your password"
                className={fieldClassName}
              />
            </div>
          </div>

          {error && (
            <p
              className="mt-5 text-center text-xs text-[#a33]"
              role="alert"
              style={SANS}
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            className="mt-8 flex w-full items-center justify-center gap-2 bg-[#111] px-6 py-3.5 text-xs tracking-[0.2em] text-white transition-colors hover:bg-[#333]"
            style={{ ...SANS, fontWeight: 400 }}
          >
            SIGN UP
            <ArrowRight className="h-3.5 w-3.5" />
          </button>

          <div className="mt-7 flex items-center gap-4">
            <div className="h-px flex-1 bg-[#e8e8e8]" />
            <span
              className="text-[10px] tracking-[0.2em] text-[#bbb]"
              style={SANS}
            >
              ALREADY A MEMBER?
            </span>
            <div className="h-px flex-1 bg-[#e8e8e8]" />
          </div>

          <button
            type="button"
            onClick={() => router.push("/input")}
            className="mx-auto mt-6 block text-xs tracking-[0.18em] text-[#555] underline decoration-[#ccc] underline-offset-4 transition-colors hover:text-[#111]"
            style={{ ...SANS, fontWeight: 400 }}
          >
            GO TO LOGIN
          </button>
        </motion.form>
      </main>
    </div>
  );
}

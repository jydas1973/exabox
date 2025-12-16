/* Copyright (c) 2025, Oracle and/or its affiliates. */

/*
   DESCRIPTION
    <short description of component this file declares/defines>

   PRIVATE CLASSES
    <list of private classes defined - with one-line descriptions>

   NOTES
    <other useful comments, qualifications, etc.>

   MODIFIED    (MM/DD/YY)
    gsundara     05/15/2025 - Creation
 */

/*
 * File        : FileEncryptor.java
 * Author      : gsundara
 * Date        : May 15, 2025
 * Description : Utility class to encrypt and decrypt files using AES-256-GCM
 */


import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.security.SecureRandom;
import java.util.Base64;

public class FileEncryptor {

    private static final String AES = "AES";
    private static final String CIPHER = "AES/GCM/NoPadding";
    private static final int GCM_TAG_LENGTH = 128; // in bits
    private static final int GCM_IV_LENGTH = 12;   // in bytes

    // 256-bit key as a Base64 string (32 bytes)
    private static final String STATIC_KEY_BASE64 = "zPq+ZKJqN1sYf2Ov0x7N8UkJFS8lj9gu8k7b4hBq7qw=";

    private static byte[] getStaticKey() {
        return Base64.getDecoder().decode(STATIC_KEY_BASE64);
    }

    public static void encrypt(String inputFile, String outputFile) throws Exception {
        SecretKeySpec key = new SecretKeySpec(getStaticKey(), AES);
        Cipher cipher = Cipher.getInstance(CIPHER);

        byte[] iv = new byte[GCM_IV_LENGTH];
        new SecureRandom().nextBytes(iv);

        GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, spec);

        try (FileInputStream fis = new FileInputStream(inputFile);
             FileOutputStream fos = new FileOutputStream(outputFile)) {

            fos.write(iv); // prepend IV to output

            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = fis.read(buffer)) != -1) {
                byte[] output = cipher.update(buffer, 0, bytesRead);
                if (output != null) fos.write(output);
            }

            byte[] finalBytes = cipher.doFinal();
            if (finalBytes != null) fos.write(finalBytes);
        }
    }

    public static void decrypt(String inputFile, String outputFile) throws Exception {
        SecretKeySpec key = new SecretKeySpec(getStaticKey(), AES);
        Cipher cipher = Cipher.getInstance(CIPHER);

        try (FileInputStream fis = new FileInputStream(inputFile)) {
            byte[] iv = new byte[GCM_IV_LENGTH];
            if (fis.read(iv) != GCM_IV_LENGTH)
                throw new IllegalArgumentException("Invalid IV");

            GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.DECRYPT_MODE, key, spec);

            try (FileOutputStream fos = new FileOutputStream(outputFile)) {
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = fis.read(buffer)) != -1) {
                    byte[] output = cipher.update(buffer, 0, bytesRead);
                    if (output != null) fos.write(output);
                }

                byte[] finalBytes = cipher.doFinal();
                if (finalBytes != null) fos.write(finalBytes);
            }
        }
    }

    public static void main(String[] args) {
        if (args.length != 3 || !(args[0].equalsIgnoreCase("encrypt") || args[0].equalsIgnoreCase("decrypt"))) {
            System.out.println("Usage: java FileEncryptor <encrypt|decrypt> <input_file> <output_file>");
            System.exit(1);
        }

        String mode = args[0];
        String inputFile = args[1];
        String outputFile = args[2];

        try {
            if (mode.equalsIgnoreCase("encrypt")) {
                encrypt(inputFile, outputFile);
                System.out.println("Encryption complete: " + outputFile);
            } else {
                decrypt(inputFile, outputFile);
                System.out.println("Decryption complete: " + outputFile);
            }
        } catch (Exception e) {
            System.err.println("Operation failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
}


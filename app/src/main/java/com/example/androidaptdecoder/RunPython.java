package com.example.androidaptdecoder;

import android.net.Uri;
import android.os.AsyncTask;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;

import java.io.File;

import javax.xml.transform.Result;

public class RunPython extends AsyncTask<String, Integer, Long> {
    @Override
    protected Long doInBackground(String... strings) {
        String fileName = strings[0];
        Python py = Python.getInstance();
        try {
            String outfile = "/storage/emulated/0/" + fileName.substring(0, fileName.length() - 3) + "png";
            py.getModule("app").callAttr("main", fileName, outfile);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}

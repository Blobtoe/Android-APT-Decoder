package com.example.androidaptdecoder;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Build.VERSION;
import android.os.Build.VERSION_CODES;
import android.os.Bundle;
import android.os.Environment;
import android.os.FileObserver;
import android.provider.DocumentsContract;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.codekidlabs.storagechooser.StorageChooser;
import com.github.chrisbanes.photoview.PhotoView;
import com.nbsp.materialfilepicker.MaterialFilePicker;
import com.nbsp.materialfilepicker.ui.FilePickerActivity;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.regex.Pattern;

import lib.folderpicker.FolderPicker;

import static java.lang.Thread.sleep;

public class MainActivity extends AppCompatActivity {

    Button infileButton;
    Button outfileButton;
    Button decodeButton;
    TextView infileTextView;
    TextView outfileTextView;
    TextView decodeTextView;
    ProgressBar progressBar;
    PhotoView photoView;

    String infile = "";
    String outfile = "";
    Float sharpen = 0f;
    Boolean combine = false;
    Float contrast = 0f;
    Boolean filter = false;
    Boolean a = false;
    Boolean b = false;


    String status = "IDLE";

    private static final int INFILE_REQUEST_CODE = 1000;
    private static final int OUTFILE_REQUEST_CODE = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if (VERSION.SDK_INT > VERSION_CODES.M && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] {Manifest.permission.WRITE_EXTERNAL_STORAGE}, 1001);
        }

        if (VERSION.SDK_INT > VERSION_CODES.M && checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] {Manifest.permission.READ_EXTERNAL_STORAGE}, 1002);
        }

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        infileButton = (Button) findViewById(R.id.infileButton);
        outfileButton = (Button) findViewById(R.id.outfileButton);
        decodeButton = (Button) findViewById(R.id.decodeButton);
        infileTextView = (TextView) findViewById(R.id.infileTextView);
        outfileTextView = (TextView) findViewById(R.id.outfileTextView);
        decodeTextView = (TextView) findViewById(R.id.decodeTextView);
        progressBar = (ProgressBar) findViewById(R.id.progressBar);
        photoView = (PhotoView) findViewById(R.id.photoView);



        infileButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    new MaterialFilePicker()
                            // Pass a source of context. Can be:
                            //    .withActivity(Activity activity)
                            //    .withFragment(Fragment fragment)
                            //    .withSupportFragment(androidx.fragment.app.Fragment fragment)
                            .withActivity(MainActivity.this)
                            // With cross icon on the right side of toolbar for closing picker straight away
                            //.withCloseMenu(true)
                            // Entry point path (user will start from it)
                            //.withPath(alarmsFolder.absolutePath)
                            // Root path (user won't be able to come higher than it)
                            //.withRootPath(externalStorage.absolutePath)
                            // Showing hidden files
                            //.withHiddenFiles(true)
                            // Want to choose only jpg images
                            .withFilter(Pattern.compile(".*\\.wav$"))
                            // Don't apply filter to directories names
                            //.withFilterDirectories(false)
                            .withTitle("Choose Audio File")
                            .withRequestCode(INFILE_REQUEST_CODE)
                            .start();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });

        outfileButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(MainActivity.this, FolderPicker.class);
                startActivityForResult(intent, OUTFILE_REQUEST_CODE);
            }
        });

        decodeButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (infile != "") {
                    if (outfile != "") {
                        decodeTextView.setText("Decoding...");
                        progressBar.setVisibility(View.VISIBLE);
                        String fileName = new File(infile).getName();

                        try {
                            copy(new File(infile), new File(getFilesDir().toString() + "/chaquopy/AssetFinder/app/" + fileName));
                        } catch (IOException e) {
                            e.printStackTrace();
                        }

                        AsyncTask.execute(new Runnable() {
                            @Override
                            public void run() {
                                Python py = Python.getInstance();
                                try {
                                    (new Thread(new Runnable()
                                    {

                                        @Override
                                        public void run()
                                        {
                                            while (!Thread.interrupted() && status == "DECODING")
                                                try
                                                {
                                                    Thread.sleep(500);
                                                    runOnUiThread(new Runnable() // start actions in UI thread
                                                    {

                                                        @Override
                                                        public void run()
                                                        {
                                                            try {
                                                                String fileContent = getFileContent();
                                                                if (fileContent.length() > 0) {
                                                                    decodeTextView.setText(fileContent);
                                                                } // this action have to be in UI thread
                                                            } catch (Exception e){
                                                                e.printStackTrace();
                                                            }
                                                        }
                                                    });
                                                }
                                                catch (InterruptedException e)
                                                {
                                                    // ooops
                                                }
                                        }
                                    })).start(); // the while thread will start in BG thread
                                    //outfile = "/storage/emulated/0/" + fileName.substring(0, fileName.length() - 3) + "png";
                                    status = "DECODING";
                                    System.out.println(infile);
                                    py.getModule("app").callAttr("main", fileName, outfile);
                                    PostDecode(outfile);
                                } catch (Exception e) {
                                    e.printStackTrace();
                                }
                            }
                        });
                    } else {
                        decodeTextView.setText("Please select an output location");
                    }
                } else {
                    decodeTextView.setText("Please select an input file");
                }
            }
        });
    }

    private String getFileContent() {
        File file = new File(getFilesDir().toString() + "/chaquopy/AssetFinder/app/" + "test.txt");
        if (!file.exists()){
            String line = "Need to add smth";
            return line;
        }
        String line = null;
        //Read text from file
        //StringBuilder text = new StringBuilder();
        try {
            BufferedReader br = new BufferedReader(new FileReader(file));
            line = br.readLine();
        }
        catch (IOException e) {
            e.printStackTrace();
            //You'll need to add proper error handling here
        }
        return line;
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == 1000 && resultCode == RESULT_OK) {
            String filePath = data.getStringExtra(FilePickerActivity.RESULT_FILE_PATH);
            infile = filePath;
            infileTextView.setText(infile);
        } if (requestCode == OUTFILE_REQUEST_CODE && resultCode == Activity.RESULT_OK) {
            outfile = data.getExtras().getString("data");
            outfileTextView.setText(outfile);
        }
    }

    public void PostDecode(String src) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                status = "IDLE";
                decodeTextView.setText("DONE");
                progressBar.setVisibility(View.INVISIBLE);

                //show origianl
                File file = new File(infile);
                File imgFile = new  File(src+"/"+file.getName().substring(0, file.getName().length()-4)+ "_original.png");
                if(imgFile.exists()){
                    Bitmap myBitmap = BitmapFactory.decodeFile(imgFile.getAbsolutePath());
                    photoView.setImageBitmap(myBitmap);
                };
            }
        });
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        switch (requestCode) {
            case 1001: {
                if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    Toast.makeText(this, "Permission Granted!", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(this, "Permission Denied.", Toast.LENGTH_SHORT).show();
                    finish();
                }
            }
            case 1002: {
                if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    Toast.makeText(this, "Permission Granted!", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(this, "Permission Denied.", Toast.LENGTH_SHORT).show();
                    finish();
                }
            }
        }
    }

    public static void copy(File src, File dst) throws IOException {
        try (InputStream in = new FileInputStream(src)) {
            try (OutputStream out = new FileOutputStream(dst)) {
                // Transfer bytes from in to out
                byte[] buf = new byte[1024];
                int len;
                while ((len = in.read(buf)) > 0) {
                    out.write(buf, 0, len);
                }
            }
        }
    }
}
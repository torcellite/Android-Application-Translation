Android-Application-Translation
===============================

#####Project Synopsis 

This is a rudimentary Google App Engine python application to translate the contents of `strings.xml`

You can use the application here - [android-app-translation](http://android-app-translation.appspot.com)

#####Example

1. General translation

        From: English
        <string name="monday">Monday</string>
        <item name="monday">Monday</item>
        To: German
        <string name="monday">Montag</string>
                <item name="monday">Montag</item>
        
2. Exclude certain XML elements
        From: English
        <string exclude="" name="monday">Monday</string>
        <item>Monday</item>
        To: German
        <string exclude="" name="monday">Monday</string>
        <item>Montag</item>

3. Translate custom tags

                From: English
                <custom-tag name="monday">Monday</custom-tag>
                <custom-tag exclude="">Monday</custom-tag>
                To: German
                <custom-tag name="monday">Monday</custom-tag>
                <custom-tag exclude="">Montag</custom-tag>


#####FAQ
######1. What does the Store Listing option do?

The Store Listing option does not escape single quotes with a `\`. This is done so that the text can be used on the Google Play Store Listing rather than a `strings.xml` file. Leaving this option unchecked will escape all single quotes so that they can be used as a `strings.xml` file.
######2. Do I need to add string and item to the list of tags?
Nope, string and item are already added by default. Just add your custom tags if any and whatever your `strings.xml` file needs translated.

#####Things that need to be fixed/built
1. A more fluid, sleek UI
2. Simultaneous translations of multiple languages
3. Direct downloads for the new strings.xml files
4. Encoding for translation from non-English languages - error while trying to parse the XML files.

#####Contributions

If you'd like to contribute to the project, feel free to fork the project make your changes, commit them to a separate branch and then perform a pull request.

Please make sure you run the source files through `pep8` before committing them.

#####Licensing
The project is licensed under the MIT License.

#####Screenshots

![screenshot1](screenshot1.png)
![screenshot2](screenshot2.png)
![screenshot3](screenshot3.png)
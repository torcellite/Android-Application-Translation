Android-Application-Translation
===============================

#####Project Synopsis 

This is a rudimentary Google App Engine python application to translate the contents of `strings.xml`

You can use the application here - [android-app-translation](http://android-app-translation.appspot.com)

#####Example

1. General translation

        From: English
        <strings name="monday">Monday</string>
        To: German
        <strings name="monday">Montag</string>
        
2. Exclude certain strings
        From: English
        <string name="monday"><!--exclude-->Monday</string>
        To: German
        <string name="monday"><!--exclude-->Monday</string>

3. If the value of a particular element is split across many lines and you want to exclude it from translation, please add <!--exclude--> for every line.
		From: English
		<string name="example">This
			Is
			A
			Multiline
			Element </string>
		<string name="example">This <!--exclude-->
			Is <!--exclude-->
			<!--exclude-->A
			Multiline<!--exclude>
			Element </string>
	In this case every word is ignored for translation except `Element`.


#####Things that need to be fixed/built
1. A more fluid, sleek UI
2. Simultaneous translations of multiple languages
3. Direct downloads for the new strings.xml files

#####Contributions

If you'd like to contribute to the project, feel free to fork the project make your changes, commit them to a separate branch and then perform a pull request.

#####Licensing
The project is licensed under the MIT License.

#####Screenshots

![screenshot1](screenshot1.png)
![screenshot2](screenshot2.png)
![screenshot3](screenshot3.png)
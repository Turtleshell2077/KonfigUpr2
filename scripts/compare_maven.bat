@echo off
rem Stage 5: the standard Maven tool for the same three packages.
rem mvn dependency:tree prints dependencies as Maven resolves them,
rem with -Dverbose it also shows the packages that Maven left out.
rem Needs Maven (mvn) in PATH and the Internet.
cd /d "%~dp0.."
set TREE=org.apache.maven.plugins:maven-dependency-plugin:3.11.0:tree

echo.
echo ===== 1. spring-context 6.1.12
call mvn -B -ntp -f examples/maven/spring-context/pom.xml %TREE%
call mvn -B -ntp -f examples/maven/spring-context/pom.xml %TREE% -Dverbose

echo.
echo ===== 2. okhttp 4.12.0
call mvn -B -ntp -f examples/maven/okhttp/pom.xml %TREE%
call mvn -B -ntp -f examples/maven/okhttp/pom.xml %TREE% -Dverbose

echo.
echo ===== 3. guava 33.3.1-jre: all packages, then without "annotations"
call mvn -B -ntp -f examples/maven/guava/pom.xml %TREE%
call mvn -B -ntp -f examples/maven/guava/pom.xml %TREE% "-Dexcludes=*:*annotations*"

echo.
pause

$noteA = "1188.995"
$noteB = "1334.601"
$noteC = "1413.961"
$noteD = "1587.117"
$noteE = "1781.479"
$noteF = "1887.411"
$noteLowG = "1059.274"
$noteHighG = "2118.547"

$BeepList = @(
     @{ Pitch = $noteLowG; Length = 300; };
     @{ Pitch = $noteLowG; Length = 200; };
     @{ Pitch = $noteA; Length = 500; };
     @{ Pitch = $noteLowG; Length = 500; };
     @{ Pitch = $noteC; Length = 500; };
     @{ Pitch = $noteB; Length = 950; };
     @{ Pitch = $noteLowG; Length = 300; };
     @{ Pitch = $noteLowG; Length = 200; };
     @{ Pitch = $noteA; Length = 500; };
     @{ Pitch = $noteLowG; Length = 500; };
     @{ Pitch = $noteD; Length = 500; };
     @{ Pitch = $noteC; Length = 950; };
     @{ Pitch = $noteLowG; Length = 300; };
     @{ Pitch = $noteLowG; Length = 200; };
     @{ Pitch = $noteHighG; Length = 500; };
     @{ Pitch = $noteE; Length = 500; };
     @{ Pitch = $noteC; Length = 500; };
     @{ Pitch = $noteB; Length = 500; };
     @{ Pitch = $noteA; Length = 500; };
     @{ Pitch = $noteF; Length = 300; };
     @{ Pitch = $noteF; Length = 200; };
     @{ Pitch = $noteE; Length = 500; };
     @{ Pitch = $noteC; Length = 500; };
     @{ Pitch = $noteD; Length = 500; };
     @{ Pitch = $noteC; Length = 900; };
 );

 # You can modify the variable $num_Loop for your convenience
 $num_Loop = 2; 
 Foreach ($i in 1..$num_Loop) {  
     foreach ($Beep in $BeepList) {  
         [System.Console]::Beep($Beep['Pitch'], $Beep['Length']);  
     }  
 }

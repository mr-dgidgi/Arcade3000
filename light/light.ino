// LED Controlling for Arcade3000 Cabinet

// Array to store each light with : [pin][brightness][program][moving][delay]
const int LightNumber = 3;
int Lights[LightNumber][5] = {
    {3,0,0,0,0},
    {5,0,0,0,0},
    {6,0,0,0,0}
};

bool Startup=true;

void setup() {
    // Configurer la broche LED comme sortie
    for(int i=0;i<LightNumber;i++) {
        pinMode(Lights[i][0], OUTPUT);
    }
    for(int i=0;i<LightNumber;i++) {
        analogWrite(Lights[i][0], Lights[i][1]);
    }
}

void loop() {
/* 
program :
0 : turned of
1 : 1/4 power
2 : 2/4 power
3 : 3/4 power
4 : full power
moving : 
0 : stable
1 : dim up slow
2 : dim down slow
3 : dim up quick
4 : dim down quick
5 : instant
*/
  if (Startup) && (Lights[i][4] == 0){
    if (Lights[i][1] == 0){
      for(int i=0;i<LightNumber;i++) {
        Lights[i][2] = 4;
        Lights[i][3] = 1;
        Lights[i][4] = 1;
      }
      else if (Lights[i][1] > 240){
        for(int i=0;i<LightNumber;i++) {
          Lights[i][2] = 1;
          Lights[i][3] = 5;
          Lights[i][4] = 100;
        }
      }
      else {
        delay(1000);
        for(int i=0;i<LightNumber;i++) {
          Lights[i][2] = 4;
          Lights[i][3] = 3;
          Lights[i][4] = 10;
        }
        Startup = false;
    }
  }
  else {
    for(int i=0;i<LightNumber;i++) {
      //check movement
      switch (Lights[i][3]) {
        // if stable
        case 0:
            Randomized(&Lights[i][2],&Lights[i][3],&Lights[i][4]);
          break;

        //if dim up        
        case 1:
        case 3:
          if (Lights[i][1]<Lights[i][2]*50+50) {
            ContinueDim(Lights[i][0],&Lights[i][1],Lights[i][3]);
          }
          else {
            Randomized(&Lights[i][2],&Lights[i][3],&Lights[i][4]);
          }
          break;
        
        //if dim down
        case 2:
        case 4:
          if (Lights[i][1]>Lights[i][2]*50) {
            ContinueDim(Lights[i][0],&Lights[i][1],Lights[i][3]);
          }
          else {
            Randomized(&Lights[i][2],&Lights[i][3],&Lights[i][4]);
          }
          break; 

        // if instant 
        case 5:
          if (Lights[i][1]!=Lights[i][2]*50) {
            ContinueDim(Lights[i][0],&Lights[i][1],Lights[i][3]);
          }
          else {
            Randomized(&Lights[i][2],&Lights[i][3],&Lights[i][4]);
          }
      }

      delay(10);
    }
  }
}

void ContinueDim(int PinNumber, int* PinValue, int DimType) {
  switch (DimType) {
    case 0:
      *PinValue = *PinValue;
      break;
    case 1:
      *PinValue = *PinValue+5;
      break;
    case 2:
      *PinValue = *PinValue-5;
      break;
    case 3:
      *PinValue = *PinValue+25;
      break;
    case 4:
      *PinValue = *PinValue-25;
      break;
  }
  analogWrite(PinNumber,*PinValue);

}

void Randomized(int* Prog, int* Speed, int* Rand) {
  if (*Rand >0) {
    (*Rand)--;
  }
  else {
  // random Program
    *Prog=random(0,4);
  // random dim/speed
    *Speed=random(0,5);
  // random random
    if (*Prog==0){
      *Rand = random(0,20);
    }
    else {
      *Rand = random(0,100);
    }
  }
}
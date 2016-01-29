;B3D Extension Module


;Parameters:
;Scene = The model name
;CamToRead = The camera name in the scene
;Props = True - The camera is loaded with all the properties
;        False - The camera is loaded like a pivot

;Read Camera In The Scene
Function ReadCamera(Scene,CamToRead$ = 0,Props = False)
	If Scene = 0 Then Return
	Children = CountChildren(Scene)
		
	For Child = 1 To Children

		ChildName$ = EntityName$(GetChild(Scene,Child))
		ChildName$ = Replace(ChildName$,Chr$(13),Chr$(10))
		
		If Instr(ChildName$,"CAMS")
			Offset = Instr(ChildName$,"CAMS",1)+5
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			CamName$ = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			CamType% = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			CamZoom# = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			If (CamType% = 1)
				CamZoom# = CamZoom# * 0.0458 ;persp
			Else
				CamZoom# = CamZoom# * 0.0275 ;ortho
			EndIf
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			CamNear# = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			CamFar# = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			If (CamToRead$ = CamName$)
				CamReaded = CreateCamera(GetChild(Scene,Child))
				If (Props = True)
					NameEntity CamReaded,CamName$
					CameraProjMode CamReaded,CamType%
					CameraZoom CamReaded,CamZoom#
					CameraRange CamReaded,CamNear#*10,CamFar#*10
				EndIf
				Return CamReaded
			EndIf
		EndIf
	Next
End Function


;Parameters:
;Scene = The model name

;Read AmbientLight Of The Scene
Function ReadAmbientLight(Scene)
	If Scene = 0 Then Return
	Children = CountChildren(Scene)
		
	For Child = 1 To Children

		ChildName$ = EntityName$(GetChild(Scene,Child))
		ChildName$ = Replace(ChildName$,Chr$(13),Chr$(10))
		
		If Instr(ChildName$,"AMBI")
			Offset = Instr(ChildName$,"AMBI",1)+5
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			AmbLigColor% = Mid$(ChildName$,Offset,NewOffset-Offset)
					
			AmbLigR% = AmbLigColor% Shr 16 And %11111111
			AmbLigG% = AmbLigColor% Shr 8 And %11111111
			AmbLigB% = AmbLigColor% And %11111111
					
			AmbientLight AmbLigR%,AmbLigG%,AmbLigB%
		EndIf
	Next
End Function


;Parameters:
;Scene = The model name
;LigToRead = The light name in the scene
;Props = True - The light is loaded with all the properties
;        False - The light is loaded like a pivot

;Read Light In The Scene
Function ReadLight(Scene,LigToRead$ = 0,Props = False)
	If Scene = 0 Then Return
	Children = CountChildren(Scene)
		
	For Child = 1 To Children

		ChildName$ = EntityName$(GetChild(Scene,Child))
		ChildName$ = Replace(ChildName$,Chr$(13),Chr$(10))
		
		If Instr(ChildName$,"LIGS")
			Offset = Instr(ChildName$,"LIGS",1)+5
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			LigName$ = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			LigType% = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			LigAngle# = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			LigColor% = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			Offset = NewOffset+1
			NewOffset = Instr(ChildName$,Chr$(10),Offset)
			LigRange# = Mid$(ChildName$,Offset,NewOffset-Offset)
			
			If (LigToRead$ = LigName$)
				LigReaded = CreateLight(LigType%,GetChild(Scene,Child))
				If (Props = True)
					NameEntity LigReaded,LigName$
					LightConeAngles LigReaded,0,LigAngle#
					
					LigR% = LigColor% Shr 16 And %11111111
					LigG% = LigColor% Shr 8 And %11111111
					LigB% = LigColor% And %11111111
					
					LightColor LigReaded,LigR%,LigG%,LigB%
					LightRange LigReaded,LigRange#
				EndIf
				Return LigReaded
			EndIf
		EndIf
	Next
End Function
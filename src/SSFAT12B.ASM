; Slither's Simple FAT12 Bootloader
; Written by Nathaniel Yodock
; For use with Slither. (https://github.com/I8087/Slither/)
; Licensed under BSD 2-Clause License. (See LICENSE for more detail.)

; This is a simple FAT12 bootloader for 16-bit real mode kernel's. In theory,
; this bootloader should be able to dynamically load a kernel from any
; FAT12 formatted disk, so long as the EPBP is properly setup. It can only load
; kernel's by their SFN in the root directory, although the bootloader can load
; files with sizes greater than 64 KiB.

; Define that this is 16-bit code.
BITS 16

; Short jump over the EBPB.
jmp short start
nop

; Extended BIOS Parameter Block.
; The default values are hardcoded in the even that Slither doesn't change them.
; The default values reflect that of an IBM PC 3.5" 1.44 MiB Floppy Disk.
OEM_Label             db "        "
Bytes_Per_Sector      dw 512
Sectors_Per_Cluster   db 1
Reserved_Sectors      dw 1
FATs                  db 2
Dir_Entries           dw 244
Logical_Sectors       dw 2880
Media_ID              db 240
Sectors_Per_FAT       dw 9
Sectors_Per_Track     dw 18
Sides                 dw 2
Hidden_Sectors        dd 0
LBA_Sectors           dd 0
Drive_Number          db 0
Windows_NT_Flag       db 0
Signature             db 41
Volume_ID             dd 0
Volume_Label          db "           "
Identifier            db "FAT12   "

; Kernel-dependent variables.
; The default values are hardcoded in the even that Slither doesn't change them.
kernel_name db "KERNEL  SYS"
kernel_segment dw 0x1000
kernel_offset dw 0x0000

; Error message.
error_msg db "BOOTLOADER ERROR!", 0

; Start of the bootloader.
start:

    ; setup a stack 16 KiB after the bootloader with 2KiB of stack space.
    ; bootloader location (0x7c00) + 16 Kib + size of bootloader (512 bytes).
    mov ax, 0x0BE0
    mov ss, ax
    mov sp, 0x0400

    ; Setup data segment.
    mov ax, 0x07c0
    mov ds, ax
    mov es, ax

    ; Get drive parameters.
    mov [Drive_Number], dl
    mov ah, 0x08
    int 0x13

    ; INT 0x13 messes with the ES.
    push ds
    pop es

    ; Save sectors per track.
    xor ch, ch
    mov [Sectors_Per_Track], cx

    ; Save the number of heads.
    inc dh
    shr dx, 8
    mov [Sides], dx

    ; Convert Root Directory LBA to CHS.
    ; Root Directory = (Sectors_Per_FAT * FATs) + Reserved_Sectors
    xor dx, dx
    xor ah, ah
    mov al, [FATs]
    mul word [Sectors_Per_FAT]
    add ax, [Reserved_Sectors]
    call toCHS

    ; Save the head number.
    push dx

    ; Get the number of root directory sectors to load.
    ; Root Directory Sectors = (Dir_Entries * 32) / Bytes_Per_Sector
    xor dx, dx
    mov ax, [Dir_Entries]
    shl ax, 5
    div word [Bytes_Per_Sector]

    ; Restore the head number.
    pop dx

; Load the root directory.
load_root:

    ; Load the Root Directory into the disk buffer.
    stc
    mov ah, 0x02
    mov dl, [Drive_Number]
    mov bx, disk_buffer
    int 0x13

    ; If everything is good, move on. if not,
    ; reset the disk. If that fails, throw an error.
    jnc find_kernel
    call resetDisk
    jnc load_root
    jmp disk_error

; Search through the root directory for the kernel's SFN.
find_kernel:

    ; Does it tho? Did the code mess with it?
    ; INT 0x13 messes with the ES.
    push ds
    pop es

    ; Setup a counter to loop through each directory entry.
    mov cx, [Dir_Entries]

    ; Point to the disk buffer which contains the root directory in memory.
    mov si, disk_buffer

    ; Added to the disk buffer to go the the next directory entry.
    ; Entry Size - SFN = file entry offset
    mov ax, 21

    ; Make sure to read left to right.
    cld

.loop:
    ; Save the loop counter.
    push cx

    ; Check the SFN for this entry and see if it's the kernel.
    mov di, kernel_name
    mov cx, 11
    rep cmpsb
    je get_first_cluster

    ; This isn't the kernel.
    ; Add the leftover offset (CX) to the file entry offset (AX).
    add cx, ax
    add si, cx

    ; Restore the loop counter.
    pop cx

    ; Loop if there's still unread directory entries.
    loop .loop

    ; Didn't find the kernel!
    jmp disk_error

; Get the start of the cluster chain in the kernel's directory entry.
get_first_cluster:

    ; Remove the loop counter from the stack.
    pop cx

    ; Point to the start of the kernel's cluster and get it.
    mov ax, 15
    add si, ax
    mov ax, [si]

    ; Save the first cluster.
    push ax

; Load the FAT into the disk buffer.
load_FAT:
    ; Convert the First FAT's LBA to CHS.
    ; First FAT = Reserved_Sectors
    mov ax, [Reserved_Sectors]
    call toCHS

    ; Load the First FAT into the disk buffer.
    stc
    mov ax, [Sectors_Per_FAT]
    mov ah, 0x02
    mov dl, [Drive_Number]
    mov bx, disk_buffer
    int 0x13

    ; If everything is good, move on. if not,
    ; reset the disk. If that fails, throw an error.
    jnc setup_kernel_mem
    call resetDisk
    jnc load_FAT
    jmp disk_error

; Setup the kernel buffer. This is where the kernel will be loaded into memory.
setup_kernel_mem:

    ; Point to kernel buffer.
    mov bx, [kernel_segment]
    mov es, bx
    mov bx, [kernel_offset]

    ; Restore the first cluster.
    pop ax

; Get the First Cluster Sector's LBA and convert it to CHS.
get_cluster:

    ; Save the cluster.
    push ax

    ; Get the cluster offset so it can be read from the FAT.
    ; Cluster Offset = (Cluster-2) * Sectors_Per_Cluster.
    sub ax, 2
    xor dh, dh
    mov dl, [Sectors_Per_Cluster]
    mul dx

    ; Save the Cluster Offset.
    push ax

    ; Get the starting data sector of the cluster.
    ; First Cluster Sector = Root Directory Start + Root Directory Sectors
    ;                        + Cluster Offset

    ; Calculate the start of the Root Directory.
    ; Root Directory Start = (Sectors_Per_FAT * FATs) + Reserved_Sectors
    xor dx, dx
    xor ah, ah
    mov al, [FATs]
    mul word [Sectors_Per_FAT]
    add ax, [Reserved_Sectors]

    ; Restore the Cluster Offset.
    pop dx

    ; Root Directory Start + Cluster Offset.
    add ax, dx

    ; Save Root Directory Start + Cluster Offset.
    push ax

    ; Calculate the number of Root Directory Sectors.
    ; Root Directory Sectors = (Dir_Entries * 32) / Bytes_Per_Sector
    xor dx, dx
    mov ax, [Dir_Entries]
    shl ax, 5
    div word [Bytes_Per_Sector]

    ; Restore Root Directory Start + Cluster Offset.
    pop dx

    ; Root Directory Sectors + Root Directory Start + Cluster Offset
    add ax, dx

    ; Convert First Cluster Sector's LBA to CHS.
    call toCHS

; Load the Cluster's sector(s) into the kernel buffer.
load_cluster:

    ; Save the registers.
    pusha

    ; Load the Cluster's sector(s) into the kernel buffer.
    stc
    mov ah, 0x02
    mov al, [Sectors_Per_Cluster]
    mov dl, [Drive_Number]
    int 0x13

    ; If everything is good, move on. if not,
    ; reset the disk. If that fails, throw an error.
    jnc increase_kernel_buffer
    call resetDisk
    popa
    jnc load_cluster
    jmp disk_error

; Increase the kernel buffer after loading the Cluster's sectors.
increase_kernel_buffer:

    ; Restore the registers.
    popa

    ; Increase the kernel buffer.
    ; kernel buffer += Sectors_Per_Cluster * Bytes_Per_Sector
    xor dx, dx
    xor ah, ah
    mov al, [Sectors_Per_Cluster]
    mul word [Bytes_Per_Sector]
    add bx, ax

    ; If the kernel buffer's offset didn't overflow, continue on and find
    ; the next cluster in the chain.
    jnc next_cluster

    ; If the kernel buffer's offset overflowed,
    ; the kernel buffer's segment should be increase by 64KiB.
    ; kernel buffer's segment += (0x10000 / 16)
    mov ax, es
    add ax, 0x1000
    mov es, ax

; Find the next cluster in the chain.
next_cluster:

    ; Restore the cluster.
    pop ax

    ; Save the cluster
    push ax

    ; cluster offset = cluster * 1.5
    mov dx, ax
    shr dx, 1
    add ax, dx

    ; Point to the disk buffer.
    mov si, disk_buffer

    ; Point to the next cluster in the FAT.
    add si, ax

    ; Get our next cluster from the FAT.
    mov ax, [si]

    ; Get the original cluster.
    pop dx

    ; Check to see if the original cluster was odd or even.
    and dx, 1
    jz even_cluster

; The original cluster was odd so we need to remove the lowest nibble.
odd_cluster:

    shr ax, 4
    jmp check_cluster

; The original cluster was even so we need to remove the highest nibble.
even_cluster:

    and ax, 0x0FFF

; Check to see if the cluster chain still needs to continue.
check_cluster:

    ; Check to see if this cluster is bad.
    cmp ax, 0x0FF7
    je disk_error

    ; Check to see if this is the end of the cluster chain.
    cmp ax, 0x0FF8
    jb get_cluster

; Setup the segments and jump to the where the kernel was loaded.
goto_kernel:

    ; Save the location of the kernel.
    push word [kernel_segment]
    push word [kernel_offset]

    mov dl, [Drive_Number]

    ; Setup the segments for the kernel.
    mov ax, [kernel_segment]
    mov ds, ax
    mov es, ax
    mov gs, ax
    mov fs, ax

    ; Clear out the registers.
    xor ax, ax
    xor bx, bx
    xor cx, cx
    xor dh, dh
    mov si, ax
    mov di, ax

    ; Far jump to the location of the kernel to properly setup the code segment.
    retf

    ; If the kernel returns to the bootloader, it will go right into stop.

; Hangs the proccesor indefinetely.
stop:

    ; Disable interrupts and halt the processor.
    cli
    hlt

; Displays an error message and halts the bootloader.
disk_error:

    ; Point to the error message and prepare to display it on the screen.
    mov si, error_msg

    ; Make sure to read from left to right.
    cld

    ; Setup the BIOS interrupt information.
    mov ah, 0x0E
    xor bx, bx

; Loop until the null character is found in the error message.
.loop:

    ; Load a byte from the error message and increase the pointer.
    lodsb

    ; Finish displaying the error message if the byte's a null character.
    cmp al, 0
    je stop

    ; Display the byte on the screen.
    int 0x10

    ; Get another byte from the error message.
    jmp .loop

; Bootloader's reset disk function.
; Recalibrates the disk in the event of a disk error.
; IN: N/A
; OUT: CF - Clear if successful, otherwise it failed.
resetDisk:

    ; Save the caller's registers.
    pusha

    ; Reset the disk.
    stc
    xor ax, ax
    mov dl, [Drive_Number]
    int 0x13

    ; Restore the caller's registers.
    popa

    ; Return to the caller.
    ret

; Bootloader's LBA to CHS function.
; Converts LBA to CHS for BIOS disk functions.
; IN: AX - LBA
; OUT: CL - Sector Number
;      CH - Cylinder Number
;      DH - Head Number
toCHS:

    ; Save the caller's BX register.
    push bx

    ; Save the LBA for later use.
    push ax

    ; Find the Sector Number.
    ; Sector Number = (LBA % Sectors_Per_Track) + 1
    xor dx, dx
    div word [Sectors_Per_Track]
    inc dl

    ; Move the Sector Number to the appropriate return register.
    mov cl, dl

    ; Find the Cylinder Number and Head Number.
    ; Cylinder Number = (LBA / Sector_Per_Tracks) / Sides
    ; Head Number = (LBA / Sector_Per_Tracks) % Sides
    xor dx, dx
    div word [Sides]
    mov ch, al
    shl dx, 8

    pop ax
    pop bx
    ret

; Make the bootloader the size of one sector by padding the remaining space
; with zero's and adding the boot signature at the last two bytes.
times 510-($-$$) db 0
dw 0xAA55

; The disk buffer is 16KiB in size and starts immediately after the booloader.
disk_buffer:

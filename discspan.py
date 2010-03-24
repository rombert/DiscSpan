#! /usr/bin/python

import os, sys, os.path, math, popen2, tempfile, dbus, readline


def discover():

  # get a connection to the system bus
  
  drives = []
  discs = {
  'dvd_r' : 4.38 * 1024 * 1024 *1024,
  'dvd_rw' : 4.38 * 1024 * 1024 *1024,
  'dvd_plus_r' : 4.37 * 2 * 1024 * 1024 *1024,
  'dvd_plus_rw' : 4.37  * 1024 * 1024 *1024,
  'dvd_plus_r_dl':  4.37 * 2 * 1024 * 1024 *1024,
  'dvd_plus_rw_dl':  4.37 * 2 * 1024 * 1024 *1024,


#  bd_re      If someone can test this with these new formats,
#  hddvd_rw   let me know!  I need values for their capacity
#  bd_r
#  hddvd_r
  }
  
  bus = dbus.SystemBus ()

  hal_obj = bus.get_object ('org.freedesktop.Hal', '/org/freedesktop/Hal/Manager')
  hal = dbus.Interface (hal_obj, 'org.freedesktop.Hal.Manager')
  
  udis = hal.FindDeviceByCapability ('volume')
  drives = {}
  for udi in udis:

    dev_obj = bus.get_object ('org.freedesktop.Hal', udi)
    dev = dbus.Interface (dev_obj, 'org.freedesktop.Hal.Device')
    parent_obj = bus.get_object ('org.freedesktop.Hal', dev.GetProperty("info.parent"))
    parent = dbus.Interface (parent_obj, 'org.freedesktop.Hal.Device')
    
    if parent.GetProperty ('storage.hotpluggable') or 'storage.cdrom' in parent.GetProperty('info.capabilities'):
        try:
          if dev.GetProperty('volume.disc.type') in discs.keys():
            device_name = dev.GetProperty ('block.device')
            capacity = discs[dev.GetProperty('volume.disc.type')]
            drive_name = parent.GetProperty('info.product')
            drives[device_name] = [capacity, drive_name]
            print "Found a %s in %s (%s)" % (dev.GetProperty('volume.disc.type'), device_name, drive_name  )
        except:
          continue
        else:
          continue
              
  return drives

def RunCmd(command):
    
    print "Running command : %s" % command
    app = popen2.Popen4(command,bufsize=0)
    infile = app.fromchild
    output= []
    while app.poll() == -1:
        while 1:
          
          try:
            line = infile.readline()
          except:
            pass
            
          if not line: break
          output.append(line)
          print line,
        infile.close()     

        
    if app.poll() > 0 :
     
         print "There was an error running %s." % command
         sys.exit(1)

    return output


def build_list(files, dvd_capacity):
 
  file_count = 1
  disc_size = 0
  disc_list = []
  disc_files = []
  outfiles = []
 
  for file in files:
    
    if not os.path.islink(file):    
      size = os.path.getsize(file)
      disc_size = disc_size + size
    else:
      size = 0
    
    if disc_size >= dvd_capacity:
      disc_list.append(disc_files)
      disc_size = 0
      disc_size = disc_size + size
      disc_files = []
      disc_files.append(file)

    else:
      disc_files.append(file)
      
  disc_list.append(disc_files)

  return (disc_list)
    

def burn(disc, dir, drive, speed, disc_num, total_disc):
  
  if disc_num ==1:
    msg = "\nReady to burn disc %s/%s.  Press Enter"  % (disc_num, total_disc )
  else:
    msg = "\nInsert Empty Disc %s/%s and Press Enter\n" % (disc_num, total_disc )

  input=raw_input(msg)
  
  list = ""
  for file in disc:
    file_on_disc = file.replace(dir, "")
    list = list + "%s=%s\n" % (file_on_disc, file)
  fd, temp_list = tempfile.mkstemp(suffix=".discspanlist")
  output = open(temp_list, 'w')
  output.write(list)
  output.close()
  burn_cmd = "growisofs -Z %s -speed=%s -use-the-force-luke=notray" \
              " -use-the-force-luke=tty  -gui" \
              " -V DiscSpanData -A DiscSpan -p Unknown -iso-level 3" \
              " -l -r -hide-rr-moved -J -joliet-long" \
              " -graft-points --path-list %s" %(drive, speed, temp_list)
  
  if len(sys.argv) >=2 :
  
    if sys.argv[1] == "test":

      burn_cmd = "growisofs -Z %s -speed=%s -use-the-force-luke=notray" \
                  " -use-the-force-luke=tty  -gui -use-the-force-luke=dummy" \
                  " -V DiscSpanData -A DiscSpan -p Unknown -iso-level 3" \
                  " -l -r -hide-rr-moved -J -joliet-long" \
                  " -graft-points --path-list %s" %(drive, speed, temp_list)


  RunCmd(burn_cmd)
  os.unlink(temp_list)
  RunCmd("eject")
  
try:

  valid = False
  while valid == False:
    dir = raw_input('Which directory would you like to backup?\n')
  
    if os.path.isdir(dir):
      valid = True
    else:
      print "You must enter a valid directory."
      valid = False
  
  
  
  
  
  input = raw_input("\nPlease put a blank DVD in your drive so I can attempt to autodetect the device name and press Enter\n")
  
  drives = discover()
  
  
  if len(drives) == 1:
    statement = '\nUsing %s (%s) as your dvd burner, if this is wrong enter a valid one or press Enter to continue\n' % (drives.keys()[0], drives[drives.keys()[0]][1])
    
  elif len(drives) > 1:
    statement ='\nFound these capable dvd burners %s, enter one\n' % " ".join(drives).keys()
  else:
    statement ='\nNo dvd burner(s) found.  You may attempt to manually enter a device name\n'
  
  drive_input=raw_input(statement)
  
  if drive_input == "" and len(drives) ==1:
    drive = drives.keys()[0]
  else:
    drive = drive_input
    
  
  
  total_size = 0
  disc_capacity = int(drives[drive][0])
  
  print "The disc capacity of the disc in %s (%s) is %s GB" % (drive, drives[drive][1], str(disc_capacity / 1073741824.0) )
    
  
  speed = raw_input("\nEnter the speed which your drive and media support and press Enter\n")
  
  
  if dir[len(dir)-1:] != "/":
    dir = dir + "/"
  
  
    
  
  file_list = []
  
  for path, dirs, files in os.walk(dir):
    for filename in files:
       file_list.append(os.path.join(path, filename))
       print os.path.join(path, filename)
  
  
  file_list.sort()
  
  for file in file_list:
    if not os.path.islink(file):
      size = os.path.getsize(file)
      total_size = total_size + size
      if size >= disc_capacity:
        print "%s is larger than the capacity of the disc.  I can not span large files across discs."
        sys.exit(1)
      
  
  num_discs = int( math.ceil (total_size / disc_capacity) )
  
  
  (discs) = build_list(file_list, disc_capacity)
  
  print "\nNumber of %s's required to burn: %s" % ("dvd", len(discs))
  
  file_count = 0
  
  for disc in discs:
    file_count = file_count + len(disc)
  
  print "\nSanity Check\n"
  print "Total files in directory", len(file_list)
  print "Total files in all discs: ", file_count
  
  
  disc_num = 1 
  for disc in discs:
    burn(disc,dir, drive, speed, disc_num, len(discs))
    disc_num = disc_num + 1


except KeyboardInterrupt:
  print "\nUser Interrupted.\n"
  sys.exit(1)




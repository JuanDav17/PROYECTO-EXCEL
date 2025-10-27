import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UploaderPageComponent } from './uploader-page.component';

describe('UploaderPageComponent', () => {
  let component: UploaderPageComponent;
  let fixture: ComponentFixture<UploaderPageComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UploaderPageComponent]
    });
    fixture = TestBed.createComponent(UploaderPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
